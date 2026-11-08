#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自建流量分析接口（api/analytics.js / api/analytics-stats.js）本地端到端测试

不碰线上环境：
  * 起一个假 PostgREST（本地 HTTP 服务）冒充 Supabase，接收写库请求
  * 起一个本地 node 服务，挂载仓库里的 api/analytics.js 与 api/analytics-stats.js
    （用真实 handler，不用 mock 逻辑，所以校验/限流/降级路径都被覆盖）
  * 用 http.client 打真实 HTTP 请求，逐条断言

覆盖场景：
  1. 正常写入 → 204，且落库行里 PII 键（email 等）已被剔除
  2. 缺 event / 非法 event → 400
  3. GET → 405
  4. 超大 payload → 413
  5. 限流 → 429
  6. 表不存在（PostgREST 返回 404）→ 降级 204，不 500
  7. analytics-stats 未授权 → 401；带管理员 token → 200

用法：python3 tools/test_analytics_api.py
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import http.client
import http.server
import socketserver
import socket

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NODE_HARNESS = r"""
const http = require('http');
const path = require('path');
const REPO = process.env.CW_REPO;
const analytics = require(path.join(REPO, 'api', 'analytics.js'));
const stats = require(path.join(REPO, 'api', 'analytics-stats.js'));
const auth = require(path.join(REPO, 'api', '_lib', 'auth.js'));

const server = http.createServer((req, res) => {
  const u = req.url.split('?')[0];
  if (u === '/__token') {
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ token: auth.issueSession(process.env.CW_ADMIN_EMAIL || 'test@example.com') }));
    return;
  }
  let handler = null;
  if (u === '/api/analytics') handler = analytics;
  else if (u === '/api/analytics-stats') handler = stats;
  if (!handler) { res.statusCode = 404; res.end('not found'); return; }
  Promise.resolve(handler(req, res)).catch((e) => {
    try { res.statusCode = 500; res.end(String((e && e.message) || e)); } catch (_) {}
  });
});
server.listen(parseInt(process.env.CW_PORT || '0', 10), '127.0.0.1', () => {
  console.log('READY ' + server.address().port);
});
"""


class FakePostgrest(http.server.BaseHTTPRequestHandler):
    """极简 PostgREST 替身：只实现 cw_analytics / cw_admins 需要的读写"""

    state = {"missing_table": False, "inserted": [], "mode": "normal"}

    def log_message(self, *args):
        pass

    def _send(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/__missing":
            FakePostgrest.state["missing_table"] = (
                FakePostgrest.state["missing_table"] != "1"
            )
            return self._send(200, {"missing_table": FakePostgrest.state["missing_table"]})
        if path == "/__inserted":
            return self._send(200, FakePostgrest.state["inserted"])
        if path.startswith("/rest/v1/cw_admins"):
            return self._send(200, [{"email": "test@example.com"}])
        if path.startswith("/rest/v1/cw_analytics"):
            rows = [
                {
                    "ts": "2026-11-08T10:00:00+08:00",
                    "event": "page_view",
                    "city": "beijing",
                    "path": "/beijing.html",
                    "referrer": "https://www.google.com/",
                    "session_id": "sess-1",
                },
                {
                    "ts": "2026-11-08T11:00:00+08:00",
                    "event": "booking_submit",
                    "city": "shanghai",
                    "path": "/booking.html",
                    "referrer": "",
                    "session_id": "sess-2",
                },
                {
                    "ts": "2026-11-08T12:00:00+08:00",
                    "event": "page_view",
                    "city": "",
                    "path": "/index.html",
                    "referrer": "",
                    "session_id": "sess-1",
                },
            ]
            return self._send(200, rows)
        return self._send(200, [])

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        path = self.path.split("?")[0]
        if path.startswith("/rest/v1/cw_analytics"):
            if FakePostgrest.state["missing_table"]:
                return self._send(404, {"code": "42P01", "message": "relation does not exist"})
            try:
                row = json.loads(raw.decode("utf-8"))
            except Exception:
                row = {"raw": raw.decode("utf-8", "replace")}
            FakePostgrest.state["inserted"].append(row)
            return self._send(201, [dict(row, id=len(FakePostgrest.state["inserted"]))])
        return self._send(201, [])


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def wait_port(port, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
            c.request("GET", "/__ping")
            c.getresponse().read()
            c.close()
            return True
        except Exception:
            time.sleep(0.2)
    return False


def req(port, method, path, body=None, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    hdrs = dict(headers or {})
    payload = None
    if body is not None:
        payload = body if isinstance(body, (bytes, str)) else json.dumps(body)
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
        hdrs.setdefault("Content-Length", str(len(payload)))
    c.request(method, path, body=payload, headers=hdrs)
    r = c.getresponse()
    data = r.read().decode("utf-8", "replace")
    c.close()
    return r.status, data


RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(("PASS  " if ok else "FAIL  ") + name + ((" — " + detail) if detail else ""))


def main():
    # ---- 1. 假 PostgREST ----
    pg_port = free_port()
    pg = socketserver.ThreadingTCPServer(("127.0.0.1", pg_port), FakePostgrest)
    pg.daemon_threads = True
    threading.Thread(target=pg.serve_forever, daemon=True).start()
    if not wait_port(pg_port):
        print("假 PostgREST 启动失败")
        return 1

    # ---- 2. node harness（挂载真实 handler）----
    tmpdir = tempfile.mkdtemp(prefix="cw-analytics-test-")
    harness_path = os.path.join(tmpdir, "harness.js")
    with open(harness_path, "w", encoding="utf-8") as f:
        f.write(NODE_HARNESS)

    def start_harness(rate_limit):
        env = dict(os.environ)
        env.update({
            "CW_REPO": REPO,
            "CW_PORT": str(free_port()),
            "SUPABASE_URL": "http://127.0.0.1:%d" % pg_port,
            "SUPABASE_SERVICE_ROLE_KEY": "test-key",
            "SESSION_SECRET": "test-secret",
            "CW_ADMIN_EMAIL": "test@example.com",
            "ANALYTICS_RATE_LIMIT_PER_MINUTE": str(rate_limit),
        })
        proc = subprocess.Popen(
            ["node", harness_path], env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        line = proc.stdout.readline()
        if "READY" not in line:
            print("node harness 启动失败：", line)
            proc.kill()
            return None, None
        port = int(line.strip().split()[-1])
        return proc, port

    proc, port = start_harness(1000)
    if proc is None:
        return 1
    try:
        # ---- 3. 写入端点 ----
        status, _ = req(port, "POST", "/api/analytics", {
            "event": "page_view",
            "path": "/beijing.html?utm_source=google",
            "city": "beijing",
            "referrer": "https://www.google.com/",
            "session_id": "abc123",
            "ua": "Mozilla/5.0 (Macintosh)",
            "props": {"city": "beijing", "product": "airport transfer", "email": "leak@example.com",
                      "phone": "13800000000", "name": "张三", "utm_source": "google"},
        })
        check("正常写入返回 204", status == 204, "status=%s" % status)

        status, _ = req(port, "GET", "/rest/v1/../__inserted")
        st, inserted_raw = req(pg_port, "GET", "/__inserted")
        inserted = json.loads(inserted_raw)
        ok = len(inserted) == 1
        check("PostgREST 收到 1 条写入", ok, "n=%d" % len(inserted))
        if ok:
            row = inserted[0]
            props = row.get("props") or {}
            leaked = [k for k in props if k.lower() in ("email", "phone", "name", "tel")]
            check("props 中 PII 键被剔除", not leaked, "leaked=%s" % leaked)
            check("props 保留业务维度 product", props.get("product") == "airport transfer", str(props))
            check("city / path / session_id 落库正确",
                  row.get("city") == "beijing" and row.get("session_id") == "abc123"
                  and row.get("path", "").startswith("/beijing.html"),
                  str(row))

        status, _ = req(port, "POST", "/api/analytics", {"city": "beijing"})
        check("缺 event 返回 400", status == 400, "status=%s" % status)

        status, _ = req(port, "POST", "/api/analytics", {"event": "evil_event"})
        check("非法 event 返回 400", status == 400, "status=%s" % status)

        status, _ = req(port, "GET", "/api/analytics")
        check("GET 返回 405", status == 405, "status=%s" % status)

        big = "x" * (40 * 1024)
        status, _ = req(port, "POST", "/api/analytics", {"event": "page_view", "path": big})
        check("超大 payload 返回 413", status == 413, "status=%s" % status)

        # ---- 4. 表不存在 → 降级 204，不 500 ----
        req(pg_port, "GET", "/__missing")
        status, _ = req(port, "POST", "/api/analytics", {"event": "page_view", "city": "beijing"})
        check("表不存在降级返回 204（不 500）", status == 204, "status=%s" % status)
        req(pg_port, "GET", "/__missing")

        # ---- 5. 统计接口鉴权 ----
        status, body = req(port, "GET", "/api/analytics-stats")
        check("统计接口未授权返回 401", status == 401, "status=%s" % status)

        st, token_body = req(port, "GET", "/__token")
        token = json.loads(token_body)["token"]
        status, body = req(port, "GET", "/api/analytics-stats?event=page_view",
                           headers={"Authorization": "Bearer " + token})
        check("统计接口带 token 返回 200", status == 200, "status=%s" % status)
        if status == 200:
            data = json.loads(body)
            stats = data.get("stats") or {}
            check("统计返回 today / sessions7d",
                  "today" in stats and "sessions7d" in stats, str(stats))
            check("统计返回事件流 rows", isinstance(data.get("rows"), list), str(type(data.get("rows"))))
    finally:
        try:
            proc.kill()
        except Exception:
            pass

    # ---- 6. 限流（独立 harness，小阈值）----
    proc2, port2 = start_harness(2)
    if proc2 is not None:
        try:
            codes = []
            for _ in range(5):
                st, _ = req(port2, "POST", "/api/analytics", {"event": "page_view"})
                codes.append(st)
            check("同一 IP 超过阈值后返回 429", 429 in codes, str(codes))
        finally:
            try:
                proc2.kill()
            except Exception:
                pass

    pg.shutdown()

    failed = [r for r in RESULTS if not r[1]]
    print("\n%d 项检查，%d 失败" % (len(RESULTS), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

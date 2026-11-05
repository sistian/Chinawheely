#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真实 manage token 端到端验证（单次流程，不提前删单）：
下单 → 轮询确认邮件 → 取 ref+token → 查单(200/quote) → 错 token(403) → 不存在(404) → 清理。"""
import email, imaplib, json, os, re, sys, time, urllib.parse, urllib.request

API = "https://api.chinawheely.com/api"
ENV = "/Users/w/Desktop/ChinaWiFiGo houduan 9.24/.env.local"
CUST = "15527771775@qq.com"
MARK = "E2E" + str(int(time.time()))[-5:]

ok = True


def env_val(k):
    for line in open(ENV, encoding="utf-8"):
        if line.strip().startswith(k + "="):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    return None


def post_form(path, fields):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(f"{API}/{path}", data=data,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def get_json(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def rest(method, path, key, base):
    req = urllib.request.Request(f"{base}/rest/v1/{path}", method=method,
                                 headers={"apikey": key, "Authorization": f"Bearer {key}",
                                          "Prefer": "return=representation"})
    with urllib.request.urlopen(req, timeout=60) as r:
        t = r.read().decode()
        return json.loads(t) if t.strip() else None


SB, KEY, PW = env_val("SUPABASE_URL"), env_val("SUPABASE_SERVICE_ROLE_KEY"), env_val("SMTP_PASS")

print("=" * 66)
print("真实下单 → 查单 端到端验证")
print("=" * 66)

print(f"\n【1】下单（标记 {MARK}）")
st, body = post_form("booking", {
    "firstName": "CW", "lastName": MARK, "email": CUST, "phone": "15527771775",
    "city": "Beijing", "product": "airport", "vehicle": "sedan_economy",
    "date": "2026-12-20", "time": "10:00", "passengers": "2", "luggage": "2",
    "serviceType": "airport_transfer",
})
print(f"  http={st}")
if st not in (200, 302):
    print("  ❌", body[:300]); sys.exit(1)

print("\n【2】轮询确认邮件")
ref = token = None
for attempt in range(12):
    time.sleep(5)
    M = imaplib.IMAP4_SSL("imap.qq.com", 993, timeout=25)
    M.login(CUST, PW); M.select("INBOX")
    typ, data = M.search(None, 'ALL')
    ids = data[0].split() if data and data[0] else []
    admin_ref = None
    cands = []
    for mid in reversed(ids[-25:]):
        typ, msg = M.fetch(mid, '(RFC822)')
        raw = msg[0][1]
        m = email.message_from_bytes(raw)
        sub = str(email.header.make_header(email.header.decode_header(m.get('Subject') or '')))
        txt = ""
        for p in m.walk():
            if p.get_content_type() in ("text/plain", "text/html"):
                try:
                    txt += p.get_payload(decode=True).decode("utf-8", "ignore")
                except Exception:
                    pass
        # ① 管理员通知里带订单号（正文含下单标记）
        if MARK in txt or MARK in sub:
            mr = re.search(r"Order Number:\s*(CWO-\d{8}-[A-F0-9]{8})", txt)
            if mr:
                admin_ref = mr.group(1)
        # ② 客户确认邮件：主题里带订单号，正文里有 manage 链接
        mr2 = re.search(r"Your Chinawheely booking\s+(CWO-\d{8}-[A-F0-9]{8})", sub)
        if mr2:
            mt = re.search(r'manage-order\.html\?ref=([A-Za-z0-9\-]+)&(?:amp;)?token=([a-f0-9]{48})', txt)
            if mt:
                cands.append((mr2.group(1), mt.group(2)))
    M.logout()
    # 必须等 admin 通知先到（它带本次标记），再用它的订单号去配对客户确认邮件
    # ⚠ 不能在 admin 通知未到时回退到「任意客户邮件」，否则会拿到上一轮的旧邮件
    if admin_ref:
        for r_, t_ in cands:
            if r_ == admin_ref:
                ref, token = r_, t_
                break
    if ref:
        print(f"  ✅ 第 {attempt + 1} 次轮询拿到 ref={ref}（admin 通知 ref={admin_ref}）")
        break
    print(f"  ... 轮询 {attempt + 1}/12（admin_ref={admin_ref}, 客户邮件候选 {len(cands)}）")
if not ref:
    print("  ❌ 邮件里没找到 manage link")
    ok = False

print("\n【3】查单（正确 ref + token）→ 期望 200 且 quote 非 null")
if ref:
    st, r = get_json(f"{API}/order?ref={urllib.parse.quote(ref)}&token={token}")
    print(f"  http={st}")
    o = (r or {}).get("order") or {}
    q = o.get("quote")
    print(f"  quote = {json.dumps(q, ensure_ascii=False)[:280] if q else q}")
    print(f"  self_modify = {json.dumps((r or {}).get('self_modify'), ensure_ascii=False)}")
    print(f"  订单摘要: {json.dumps({k: o.get(k) for k in ['ref','status','payment_status','city','vehicle','total_cny','total_usd','pickup_date','pickup_time','pax']}, ensure_ascii=False)}")
    ok &= (st == 200)
    if q:
        print("  ✅ quote 非 null")
    else:
        print("  ❌ quote 为 null")
        ok = False

    print("\n【4】错 token → 期望 403")
    st, r = get_json(f"{API}/order?ref={urllib.parse.quote(ref)}&token={'b' * 48}")
    print(f"  http={st}  {json.dumps(r, ensure_ascii=False)[:180]}")
    ok &= (st == 403)

print("\n【5】不存在的单 → 期望 404")
st, r = get_json(f"{API}/order?ref=CWO-20261105-DEADBEEF&token={'a' * 48}")
print(f"  http={st}")
ok &= (st == 404)

print("\n【6】DB 里 quote_json 的原始形态（写入路径应存对象而非 JSON 字符串）")
if ref:
    rows = rest("GET", f"cw_orders?select=ref,quote_json,pickup_date,pickup_time,pax&ref=eq.{urllib.parse.quote(ref)}", KEY, SB)
    for r0 in (rows or []):
        q0 = r0.get("quote_json")
        print(f"  quote_json 类型 = {type(q0).__name__}")
        print(f"  预览 = {json.dumps(q0, ensure_ascii=False)[:160]}")
        print(f"  pickup_date={r0.get('pickup_date')} pickup_time={r0.get('pickup_time')} pax={r0.get('pax')}")
        if isinstance(q0, dict):
            print("  ✅ 存的是 jsonb 对象（SQL 可直接用 quote->>'total'）")
        else:
            print("  ⚠️ 仍是字符串标量（写入路径未生效）")
        if r0.get("pickup_date"):
            print("  ✅ pickup_date 已正确落库（48h 改期规则可计算）")
            ok = True
        else:
            print("  ❌ pickup_date 为空")
            ok = False

print("\n【7】清理")
if ref:
    rest("DELETE", f"cw_orders?ref=eq.{urllib.parse.quote(ref)}", KEY, SB)
    print(f"  已删 {ref}")
# 清掉本邮箱下的所有残留测试单
left0 = rest("GET", f"cw_orders?select=ref&email=eq.{urllib.parse.quote(CUST)}", KEY, SB)
for o in (left0 or []):
    rest("DELETE", f"cw_orders?ref=eq.{urllib.parse.quote(o['ref'])}", KEY, SB)
    print(f"  残留已删 {o['ref']}")
left = rest("GET", f"cw_orders?select=ref&email=eq.{urllib.parse.quote(CUST)}", KEY, SB)
print(f"  该邮箱剩余单 {len(left or [])}")
ok &= (len(left or []) == 0)

print("\n" + ("✅ 全部通过" if ok else "❌ 有失败"))
sys.exit(0 if ok else 1)

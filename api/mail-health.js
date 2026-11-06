/**
 * 邮件通道健康检查（只测 TCP 可达性，不发信）。
 *
 * 背景：2026-11-06 发现 Vercel 函数连 smtp.qq.com:465 频繁超时 / TLS 握手被掐断，
 * 导致「订单入库了但客户和后台都收不到邮件」。这个端点用来随时确认通道状态。
 *
 * GET /api/mail-health  →  {ok, checks:[{port, secure, reachable, ms, error}]}
 * 只回传端口与连通结果，不回传任何凭据。
 */
const net = require('net');

const SMTP_HOST = process.env.SMTP_HOST || '';
const SMTP_PORT = Number(process.env.SMTP_PORT || 465);
const TIMEOUT_MS = 8000;

function probe(port) {
  return new Promise(resolve => {
    const started = Date.now();
    const socket = new net.Socket();
    let done = false;
    const finish = (ok, err) => {
      if (done) return;
      done = true;
      try { socket.destroy(); } catch (e) { /* ignore */ }
      resolve({ port, reachable: ok, ms: Date.now() - started, error: err || null });
    };
    socket.setTimeout(TIMEOUT_MS);
    socket.once('connect', () => finish(true, null));
    socket.once('timeout', () => finish(false, 'timeout'));
    socket.once('error', (e) => finish(false, e.code || e.message));
    try {
      socket.connect(port, SMTP_HOST);
    } catch (e) {
      finish(false, e.code || e.message);
    }
  });
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    return res.end();
  }
  if (!SMTP_HOST) {
    res.writeHead(500);
    return res.end(JSON.stringify({ ok: false, error: 'SMTP_HOST not configured' }));
  }
  const ports = Array.from(new Set([SMTP_PORT, 465, 587, 25]));
  const checks = [];
  for (const p of ports) {
    checks.push(await probe(p));
  }
  const ok = checks.some(c => c.reachable);
  res.writeHead(200);
  return res.end(JSON.stringify({
    ok,
    host: SMTP_HOST.replace(/^(\w{2})\w+/, '$1***'),   // 只显示前两个字母
    configuredPort: SMTP_PORT,
    checks,
    checkedAt: new Date().toISOString()
  }));
};

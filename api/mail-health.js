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
const tls = require('tls');
const { sendMail } = require('./_lib/mailer');

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

/** 实测 TLS 握手 + SMTP 220 问候（真正发信前的那一步） */
function probeTls(port) {
  return new Promise(resolve => {
    const started = Date.now();
    let done = false;
    const finish = (ok, err, greeting) => {
      if (done) return;
      done = true;
      try { socket.destroy(); } catch (e) { /* ignore */ }
      resolve({ port, tls: true, reachable: ok, ms: Date.now() - started, greeting: greeting || null, error: err || null });
    };
    const socket = tls.connect({
      host: SMTP_HOST,
      port,
      servername: SMTP_HOST,
      rejectUnauthorized: false,
      timeout: TIMEOUT_MS
    }, () => {
      // 握手成功，等 SMTP 问候
      let buf = '';
      socket.once('data', d => {
        buf += d.toString('utf8');
        finish(true, null, buf.split('\r\n')[0].slice(0, 80));
      });
      socket.once('error', e => finish(false, e.code || e.message));
      setTimeout(() => finish(false, 'greeting timeout'), TIMEOUT_MS);
    });
    socket.once('timeout', () => finish(false, 'tls timeout'));
    socket.once('error', (e) => finish(false, e.code || e.message));
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
  // TLS 握手 + SMTP 问候实测（465 隐式 TLS、587 STARTTLS）
  const tlsChecks = [];
  for (const p of [465, 587]) {
    tlsChecks.push(await probeTls(p));
  }
  const ok = checks.some(c => c.reachable);
  res.writeHead(200);
  const result = {
    ok,
    host: SMTP_HOST.replace(/^(\w{2})\w+/, '$1***'),   // 只显示前两个字母
    configuredPort: SMTP_PORT,
    checks,
    tlsChecks,
    checkedAt: new Date().toISOString()
  };

  // ?send=1 → 实测一封真邮件（发给业务邮箱），把真实错误同步返回
  if (req.query && req.query.send) {
    const t0 = Date.now();
    try {
      const info = await sendMail({
        to: process.env.RECIPIENT_EMAIL,
        subject: '[Chinawheely] 邮件通道测试 ' + new Date().toISOString(),
        html: '<p>Chinawheely 邮件通道自检（可忽略）。</p>',
        text: 'Chinawheely 邮件通道自检（可忽略）。'
      });
      result.send = { ok: true, ms: Date.now() - t0, messageId: info && info.messageId };
    } catch (e) {
      result.send = {
        ok: false, ms: Date.now() - t0,
        command: e && e.command, code: e && e.code, error: e && e.message
      };
    }
  }

  return res.end(JSON.stringify(result));
};
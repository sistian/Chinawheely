// Chinawheely P2 — 后台登录（邮箱 + 密码）
// 服务端向 Supabase Auth 验证凭据，通过后签发本系统会话 token。
// 连续失败按 IP 限流，防止撞库。

const querystring = require('querystring');
const { sessionConfigured, issueSession, isAdmin } = require('../_lib/auth');
const { clientIp } = require('../_lib/fields');

const SUPABASE_URL = (process.env.SUPABASE_URL || '').replace(/\/+$/, '');
const SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim()).filter(Boolean);

const MAX_ATTEMPTS = Number(process.env.LOGIN_MAX_ATTEMPTS || 8);
const WINDOW_MS = 10 * 60 * 1000;
const attempts = new Map(); // ip -> {count, resetAt}

function setCorsHeaders(res, req) {
  const requestOrigin = req.headers.origin || req.headers.referer || '';
  let origin = '*';
  if (!ALLOWED_ORIGINS.includes('*')) {
    origin = ALLOWED_ORIGINS.includes(requestOrigin) ? requestOrigin : ALLOWED_ORIGINS[0];
  }
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Vary', 'Origin');
}

function getBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', c => body += c.toString());
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

function rateLimited(ip) {
  const now = Date.now();
  const rec = attempts.get(ip);
  if (!rec || now > rec.resetAt) {
    attempts.set(ip, { count: 1, resetAt: now + WINDOW_MS });
    if (attempts.size > 5000) attempts.clear();
    return false;
  }
  rec.count += 1;
  return rec.count > MAX_ATTEMPTS;
}

async function authSignIn(email, password) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
    method: 'POST',
    headers: {
      apikey: SERVICE_ROLE_KEY,
      Authorization: `Bearer ${SERVICE_ROLE_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password })
  });
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  return { ok: res.ok, status: res.status, data };
}

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') {
    setCorsHeaders(res, req);
    res.statusCode = 204;
    return res.end();
  }
  if (req.method !== 'POST') {
    setCorsHeaders(res, req);
    res.statusCode = 405;
    return res.end('Method Not Allowed');
  }
  if (!sessionConfigured() || !SUPABASE_URL || !SERVICE_ROLE_KEY) {
    setCorsHeaders(res, req);
    res.statusCode = 503;
    return res.end(JSON.stringify({ error: 'auth not configured' }));
  }

  const ip = clientIp(req);
  if (rateLimited(ip)) {
    setCorsHeaders(res, req);
    res.statusCode = 429;
    return res.end(JSON.stringify({ error: 'too many login attempts' }));
  }

  let data = {};
  try {
    data = querystring.parse(await getBody(req));
  } catch (e) {
    setCorsHeaders(res, req);
    res.statusCode = 400;
    return res.end(JSON.stringify({ error: 'bad request' }));
  }

  // 兼容 JSON body
  if (!data.email && req.body && typeof req.body === 'object') data = req.body;

  const email = String(data.email || '').trim().toLowerCase();
  const password = String(data.password || '');
  if (!email || !password) {
    setCorsHeaders(res, req);
    res.statusCode = 400;
    return res.end(JSON.stringify({ error: 'email and password are required' }));
  }

  const signin = await authSignIn(email, password);
  if (!signin.ok) {
    setCorsHeaders(res, req);
    res.statusCode = 401;
    return res.end(JSON.stringify({ error: 'invalid credentials' }));
  }

  const admin = await isAdmin(email);
  if (!admin) {
    setCorsHeaders(res, req);
    res.statusCode = 403;
    return res.end(JSON.stringify({ error: 'account is not an administrator' }));
  }

  const token = issueSession(email);
  setCorsHeaders(res, req);
  res.statusCode = 200;
  res.setHeader('Content-Type', 'application/json');
  return res.end(JSON.stringify({ token, email, expiresIn: 8 * 60 * 60 }));
};

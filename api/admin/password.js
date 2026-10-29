// Chinawheely P2 — 管理员修改自己的密码
// PATCH /api/admin/password  body: {currentPassword, newPassword}
// 需要 Authorization: Bearer <session token>
// 流程：校验当前密码 → 用登录返回的 access_token 调 PUT /auth/v1/user 自助改密
// 不使用 Auth admin API（避免持有管理员级 JWT）

const querystring = require('querystring');
const { requireAdmin } = require('../_lib/auth');

const SUPABASE_URL = (process.env.SUPABASE_URL || '').replace(/\/+$/, '');
const SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim()).filter(Boolean);

function setCorsHeaders(res, req) {
  const requestOrigin = req.headers.origin || req.headers.referer || '';
  const origin = ALLOWED_ORIGINS.includes('*')
    ? '*'
    : (ALLOWED_ORIGINS.includes(requestOrigin) ? requestOrigin : ALLOWED_ORIGINS[0]);
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Methods', 'PATCH, POST, OPTIONS');
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

/** 校验密码并返回 access_token */
async function signIn(email, password) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
    method: 'POST',
    headers: { apikey: SERVICE_ROLE_KEY, Authorization: `Bearer ${SERVICE_ROLE_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  if (!res.ok) return { ok: false };
  return { ok: true, token: data && data.access_token };
}

/** 用用户自己的 access_token 更新密码 */
async function updateOwnPassword(accessToken, newPassword) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    method: 'PUT',
    headers: {
      apikey: SERVICE_ROLE_KEY,
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ password: newPassword })
  });
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  if (!res.ok) {
    return { ok: false, error: (data && (data.msg || data.message || data.error)) || `HTTP ${res.status}` };
  }
  return { ok: true };
}

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') {
    setCorsHeaders(res, req);
    res.statusCode = 204;
    return res.end();
  }
  if (req.method !== 'PATCH' && req.method !== 'POST') {
    setCorsHeaders(res, req);
    res.statusCode = 405;
    return res.end('Method Not Allowed');
  }

  const auth = await requireAdmin(req);
  if (!auth.ok) {
    setCorsHeaders(res, req);
    res.statusCode = auth.status;
    res.setHeader('Content-Type', 'application/json');
    return res.end(JSON.stringify({ error: auth.error }));
  }

  let body = {};
  try {
    const raw = await getBody(req);
    if (raw) {
      try { body = JSON.parse(raw); } catch (e) { body = querystring.parse(raw); }
    }
  } catch (e) { body = {}; }

  const currentPassword = String(body.currentPassword || '');
  const newPassword = String(body.newPassword || '');
  if (!currentPassword || !newPassword) {
    setCorsHeaders(res, req);
    res.statusCode = 400;
    return res.end(JSON.stringify({ error: 'currentPassword and newPassword are required' }));
  }
  if (newPassword.length < 8) {
    setCorsHeaders(res, req);
    res.statusCode = 400;
    return res.end(JSON.stringify({ error: 'new password must be at least 8 characters' }));
  }
  if (currentPassword === newPassword) {
    setCorsHeaders(res, req);
    res.statusCode = 400;
    return res.end(JSON.stringify({ error: 'new password must be different' }));
  }

  const signin = await signIn(auth.email, currentPassword);
  if (!signin.ok) {
    setCorsHeaders(res, req);
    res.statusCode = 401;
    return res.end(JSON.stringify({ error: 'current password is incorrect' }));
  }

  const result = await updateOwnPassword(signin.token, newPassword);
  setCorsHeaders(res, req);
  res.statusCode = result.ok ? 200 : 500;
  res.setHeader('Content-Type', 'application/json');
  return res.end(JSON.stringify(result.ok ? { ok: true } : { error: result.error }));
};

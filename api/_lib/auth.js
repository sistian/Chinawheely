// Chinawheely P2 — 后台会话（HMAC 签名 token）
// 登录接口在服务端向 Supabase Auth 换 access_token，再签发本系统会话 token。
// 好处：浏览器只与 api.chinawheely.com 通信（国内可达），不直连 supabase.co（大陆 SSL 受限）。

const crypto = require('crypto');
const { select } = require('./db');

const SESSION_SECRET = process.env.SESSION_SECRET || '';
const SESSION_TTL_SEC = Number(process.env.SESSION_TTL_SEC || 8 * 60 * 60); // 8 小时

function b64url(buf) {
  return Buffer.from(buf).toString('base64')
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function b64urlDecode(str) {
  const pad = str.length % 4 === 0 ? '' : '='.repeat(4 - (str.length % 4));
  return Buffer.from(str.replace(/-/g, '+').replace(/_/g, '/') + pad, 'base64').toString('utf8');
}

function sign(payload) {
  return b64url(crypto.createHmac('sha256', SESSION_SECRET).update(payload).digest());
}

function sessionConfigured() {
  return Boolean(SESSION_SECRET);
}

/** 签发会话 token */
function issueSession(email) {
  const payload = b64url(JSON.stringify({ email: String(email).toLowerCase(), exp: Date.now() + SESSION_TTL_SEC * 1000 }));
  return `${payload}.${sign(payload)}`;
}

/** 校验会话 token */
function verifySession(token) {
  if (!token || !sessionConfigured()) return { ok: false, error: 'session not configured' };
  const parts = String(token).split('.');
  if (parts.length !== 2) return { ok: false, error: 'malformed token' };
  const [payload, sig] = parts;
  const expected = sign(payload);
  const a = Buffer.from(sig);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
    return { ok: false, error: 'bad signature' };
  }
  let data;
  try {
    data = JSON.parse(b64urlDecode(payload));
  } catch (e) {
    return { ok: false, error: 'bad payload' };
  }
  if (!data.email || !data.exp || Date.now() > data.exp) {
    return { ok: false, error: 'expired' };
  }
  return { ok: true, email: data.email };
}

function getBearer(req) {
  const raw = req.headers['authorization'] || req.headers['Authorization'] || '';
  const m = String(raw).match(/^Bearer\s+(.+)$/i);
  return m ? m[1].trim() : '';
}

/** 管理员白名单 */
async function isAdmin(email) {
  if (!email) return false;
  const res = await select('cw_admins', `email=eq.${encodeURIComponent(String(email).toLowerCase())}`, 1);
  return res.ok && res.rows.length > 0;
}

/**
 * 校验请求身份：Authorization: Bearer <session token>
 */
async function requireAdmin(req) {
  const token = getBearer(req);
  if (!token) return { ok: false, status: 401, error: 'missing authorization' };
  const v = verifySession(token);
  if (!v.ok) return { ok: false, status: 401, error: v.error };
  const admin = await isAdmin(v.email);
  if (!admin) return { ok: false, status: 403, error: 'not an administrator' };
  return { ok: true, email: v.email };
}

module.exports = { issueSession, verifySession, requireAdmin, isAdmin, sessionConfigured, getBearer, SESSION_TTL_SEC };

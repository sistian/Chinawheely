// Chinawheely P2 — 线索管理 API
// GET  /api/admin/leads        列表（筛选 + 分页 + 统计）
// PATCH /api/admin/leads        更新状态 / 备注（body: {ref, status?, admin_note?, score?}）
// 全部需要 Authorization: Bearer <session token>，且邮箱需在 cw_admins 白名单内。

const querystring = require('querystring');
const { select, update } = require('../_lib/db');
const { requireAdmin } = require('../_lib/auth');

const TABLE = 'cw_leads';
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim()).filter(Boolean);
const VALID_STATUS = ['new', 'contacted', 'confirmed', 'completed', 'lost', 'cold'];
const VALID_SCORE = ['hot', 'warm', 'cold'];

function setCorsHeaders(res, req) {
  const requestOrigin = req.headers.origin || req.headers.referer || '';
  let origin = '*';
  if (!ALLOWED_ORIGINS.includes('*')) {
    origin = ALLOWED_ORIGINS.includes(requestOrigin) ? requestOrigin : ALLOWED_ORIGINS[0];
  }
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS');
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

function json(req, res, status, obj) {
  setCorsHeaders(res, req);
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  return res.end(JSON.stringify(obj));
}

async function handleGet(req, res, query) {
  const filters = [];
  const status = (query.status || '').trim();
  const source = (query.source || '').trim();
  const city = (query.city || '').trim();
  const q = (query.q || '').trim();
  const from = (query.from || '').trim();
  const to = (query.to || '').trim();

  if (status && status !== 'all') filters.push(`status=eq.${encodeURIComponent(status)}`);
  if (source && source !== 'all') filters.push(`source=eq.${encodeURIComponent(source)}`);
  if (city && city !== 'all') filters.push(`city=ilike.*${encodeURIComponent(city)}*`);
  if (from) filters.push(`created_at=gte.${encodeURIComponent(new Date(from).toISOString())}`);
  if (to) filters.push(`created_at=lte.${encodeURIComponent(new Date(to).toISOString())}`);
  if (q) {
    // 关键词：邮箱 / 电话 / 姓名 / 参考号 / 城市（用 or 组合）
    const like = `*${q}*`;
    const clause = [
      `email.ilike.${encodeURIComponent(like)}`,
      `phone.ilike.${encodeURIComponent(like)}`,
      `name.ilike.${encodeURIComponent(like)}`,
      `ref.ilike.${encodeURIComponent(like)}`,
      `city.ilike.${encodeURIComponent(like)}`
    ].join(',');
    filters.push(`or=(${clause})`);
  }

  const limit = Math.min(Number(query.limit) || 50, 200);
  const offset = Number(query.offset) || 0;

  const listQuery = `select=*${filters.length ? '&' + filters.join('&') : ''}&order=created_at.desc&limit=${limit}&offset=${offset}`;
  const listRes = await select(TABLE, listQuery, limit);
  if (!listRes.ok) {
    return json(req, res, 500, { error: 'query failed', detail: listRes.error });
  }

  // 统计（不受分页影响）
  const statsRes = await select(TABLE, 'select=status,mail_status,source,created_at', 1000);
  const stats = { total: 0, today: 0, byStatus: {}, failedMail: 0, bySource: {} };
  if (statsRes.ok) {
    const todayStr = new Date().toISOString().slice(0, 10);
    for (const row of statsRes.rows) {
      stats.total += 1;
      stats.byStatus[row.status] = (stats.byStatus[row.status] || 0) + 1;
      stats.bySource[row.source] = (stats.bySource[row.source] || 0) + 1;
      if (row.mail_status === 'failed') stats.failedMail += 1;
      if (String(row.created_at).slice(0, 10) === todayStr) stats.today += 1;
    }
  }

  return json(req, res, 200, { rows: listRes.rows, count: listRes.rows.length, limit, offset, stats });
}

async function handlePatch(req, res, body) {
  const ref = String(body.ref || '').trim();
  if (!ref) return json(req, res, 400, { error: 'ref is required' });

  const patch = {};
  if (body.status !== undefined) {
    const s = String(body.status).trim();
    if (!VALID_STATUS.includes(s)) return json(req, res, 400, { error: 'invalid status' });
    patch.status = s;
  }
  if (body.score !== undefined) {
    const s = String(body.score).trim();
    if (s === '') patch.score = null;
    else if (!VALID_SCORE.includes(s)) return json(req, res, 400, { error: 'invalid score' });
    else patch.score = s;
  }
  if (body.admin_note !== undefined) {
    patch.admin_note = String(body.admin_note).slice(0, 2000);
  }
  if (Object.keys(patch).length === 0) return json(req, res, 400, { error: 'nothing to update' });

  const res2 = await update(TABLE, `ref=eq.${encodeURIComponent(ref)}`, patch);
  if (!res2.ok) return json(req, res, 500, { error: 'update failed', detail: res2.error });
  if (!res2.rows.length) return json(req, res, 404, { error: 'lead not found' });
  return json(req, res, 200, { ok: true, row: res2.rows[0] });
}

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') {
    setCorsHeaders(res, req);
    res.statusCode = 204;
    return res.end();
  }

  const auth = await requireAdmin(req);
  if (!auth.ok) {
    setCorsHeaders(res, req);
    res.statusCode = auth.status;
    return res.end(JSON.stringify({ error: auth.error }));
  }

  try {
    if (req.method === 'GET') {
      const query = querystring.parse((req.url || '').split('?')[1] || '');
      return await handleGet(req, res, query);
    }
    if (req.method === 'PATCH' || req.method === 'POST') {
      let body = {};
      const raw = await getBody(req);
      if (raw) {
        try { body = JSON.parse(raw); }
        catch (e) { body = querystring.parse(raw); }
      }
      if (!body.ref && req.body && typeof req.body === 'object') body = req.body;
      return await handlePatch(req, res, body);
    }
    setCorsHeaders(res, req);
    res.statusCode = 405;
    return res.end('Method Not Allowed');
  } catch (err) {
    console.error('Chinawheely admin leads error:', err && err.message);
    setCorsHeaders(res, req);
    res.statusCode = 500;
    return res.end(JSON.stringify({ error: 'internal error' }));
  }
};

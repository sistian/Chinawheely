// Chinawheely P4 — 订单管理 API（后台）
// GET   /api/admin/orders        订单列表（筛选 + 分页 + 统计）
// PATCH /api/admin/orders        更新服务状态 / 支付状态 / 备注（body: {ref, status?, payment_status?, admin_note?}）
// 全部需要 Authorization: Bearer <session token>，且邮箱需在 cw_admins 白名单内。

const querystring = require('querystring');
const { select, update } = require('../_lib/db');
const { requireAdmin } = require('../_lib/auth');
const { SERVICE_STATUS, PAYMENT_STATUS } = require('../_lib/orders');

const TABLE = 'cw_orders';
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim()).filter(Boolean);

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
  const payment = (query.payment || '').trim();
  const q = (query.q || '').trim();
  const from = (query.from || '').trim();
  const to = (query.to || '').trim();

  if (status && status !== 'all') filters.push(`status=eq.${encodeURIComponent(status)}`);
  if (payment && payment !== 'all') filters.push(`payment_status=eq.${encodeURIComponent(payment)}`);
  if (from) filters.push(`created_at=gte.${encodeURIComponent(new Date(from).toISOString())}`);
  if (to) filters.push(`created_at=lte.${encodeURIComponent(new Date(to).toISOString())}`);
  if (q) {
    const like = `*${q}*`;
    const clause = [
      `ref.ilike.${encodeURIComponent(like)}`,
      `email.ilike.${encodeURIComponent(like)}`,
      `phone.ilike.${encodeURIComponent(like)}`,
      `customer_name.ilike.${encodeURIComponent(like)}`,
      `city.ilike.${encodeURIComponent(like)}`
    ].join(',');
    filters.push(`or=(${clause})`);
  }

  const limit = Math.min(Number(query.limit) || 50, 200);
  const offset = Number(query.offset) || 0;

  const listQuery = `select=ref,created_at,status,payment_status,payment_method,email,phone,customer_name,city,product,vehicle,tier,total_cny,total_usd,pickup_date,pickup_time,pax,admin_note${filters.length ? '&' + filters.join('&') : ''}&order=created_at.desc&limit=${limit}&offset=${offset}`;
  const listRes = await select(TABLE, listQuery, limit);
  if (!listRes.ok) {
    return json(req, res, 500, { error: 'query failed', detail: listRes.error });
  }

  // 统计
  const statsRes = await select(TABLE, 'select=status,payment_status,total_cny,created_at', 1000);
  const stats = {
    total: 0, today: 0,
    byStatus: {}, byPayment: {},
    unpaid: 0, pendingValueCny: 0, paidValueCny: 0
  };
  if (statsRes.ok) {
    const todayStr = new Date().toISOString().slice(0, 10);
    for (const row of statsRes.rows) {
      stats.total += 1;
      stats.byStatus[row.status] = (stats.byStatus[row.status] || 0) + 1;
      stats.byPayment[row.payment_status] = (stats.byPayment[row.payment_status] || 0) + 1;
      if (row.payment_status === 'unpaid' || row.payment_status === 'payment_submitted') {
        stats.unpaid += 1;
        stats.pendingValueCny += Number(row.total_cny) || 0;
      }
      if (row.payment_status === 'paid') stats.paidValueCny += Number(row.total_cny) || 0;
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
    if (!SERVICE_STATUS.includes(s)) return json(req, res, 400, { error: 'invalid status' });
    patch.status = s;
  }
  if (body.payment_status !== undefined) {
    const s = String(body.payment_status).trim();
    if (!PAYMENT_STATUS.includes(s)) return json(req, res, 400, { error: 'invalid payment_status' });
    patch.payment_status = s;
  }
  if (body.payment_method !== undefined) {
    patch.payment_method = String(body.payment_method).slice(0, 20);
  }
  if (body.admin_note !== undefined) {
    patch.admin_note = String(body.admin_note).slice(0, 2000);
  }
  if (body.pickup_date !== undefined) {
    const d = String(body.pickup_date).trim();
    if (d && !/^\d{4}-\d{2}-\d{2}$/.test(d)) return json(req, res, 400, { error: 'bad pickup_date' });
    patch.pickup_date = d || null;
  }
  if (body.pickup_time !== undefined) {
    const t = String(body.pickup_time).trim();
    if (t && !/^\d{1,2}:\d{2}$/.test(t)) return json(req, res, 400, { error: 'bad pickup_time' });
    patch.pickup_time = t || null;
  }
  if (Object.keys(patch).length === 0) return json(req, res, 400, { error: 'nothing to update' });
  patch.updated_at = new Date().toISOString();

  const res2 = await update(TABLE, `ref=eq.${encodeURIComponent(ref)}`, patch);
  if (!res2.ok) return json(req, res, 500, { error: 'update failed', detail: res2.error });
  if (!res2.rows.length) return json(req, res, 404, { error: 'order not found' });
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
      return await handlePatch(req, res, body);
    }
    setCorsHeaders(res, req);
    res.statusCode = 405;
    return res.end('Method Not Allowed');
  } catch (err) {
    console.error('Chinawheely admin orders error:', err && err.message);
    setCorsHeaders(res, req);
    res.statusCode = 500;
    return res.end(JSON.stringify({ error: 'internal error' }));
  }
};

// Chinawheely P4 — 客户自助查单 / 改期 API（公开，凭订单号 + manage_token）
// GET   /api/order?ref=CWO-...&token=...        查看订单（返回脱敏信息 + 是否可自助改期）
// PATCH /api/order                              自助改期（body: {ref, token, pickup_date, pickup_time}）
// 改期遵循 48 小时规则：距出发时间不足 48 小时不可自助修改（可联系客服）。

const querystring = require('querystring');
const { getOrderByRef, updateOrder, canSelfModify, sha256 } = require('./_lib/orders');

const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim()).filter(Boolean);

function setCorsHeaders(res, req) {
  const requestOrigin = req.headers.origin || req.headers.referer || '';
  let origin = '*';
  if (!ALLOWED_ORIGINS.includes('*')) {
    origin = ALLOWED_ORIGINS.includes(requestOrigin) ? requestOrigin : ALLOWED_ORIGINS[0];
  }
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Methods', 'GET, PATCH, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
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

/** 客户可见的脱敏订单视图 */
function publicView(order) {
  return {
    ref: order.ref,
    status: order.status,
    payment_status: order.payment_status,
    city: order.city,
    product: order.product,
    vehicle: order.vehicle,
    tier: order.tier,
    total_cny: order.total_cny,
    total_usd: order.total_usd,
    currency: order.currency || 'CNY',
    pickup_date: order.pickup_date,
    pickup_time: order.pickup_time,
    pax: order.pax,
    luggage: order.luggage,
    notes: order.notes || null,
    created_at: order.created_at,
    updated_at: order.updated_at,
    quote: safeParse(order.quote_json)
  };
}

function safeParse(s) {
  if (!s) return null;
  try { return JSON.parse(s); } catch (e) { return null; }
}

/** 校验 ref + token 并取单 */
async function authOrder(ref, token) {
  ref = String(ref || '').trim().toUpperCase();
  token = String(token || '').trim();
  if (!/^CWO-\d{8}-[A-F0-9]{8}$/.test(ref)) {
    return { error: { status: 400, body: { error: 'invalid ref format' } } };
  }
  if (!/^[a-f0-9]{48}$/.test(token)) {
    return { error: { status: 400, body: { error: 'invalid token format' } } };
  }
  const res = await getOrderByRef(ref, sha256(token));
  if (!res.ok) {
    return { error: { status: 500, body: { error: 'lookup failed', detail: res.error } } };
  }
  if (!res.order) {
    return { error: { status: 404, body: { error: 'order not found' } } };
  }
  // token 过期检查
  if (res.order.manage_token_expires_at && new Date(res.order.manage_token_expires_at).getTime() < Date.now()) {
    return { error: { status: 403, body: { error: 'token expired, please contact support' } } };
  }
  return { order: res.order };
}

function pickupDateTime(order) {
  if (!order.pickup_date) return null;
  const t = order.pickup_time || '00:00';
  return `${order.pickup_date}T${String(t).padStart(5, '0')}:00+08:00`;
}

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') {
    setCorsHeaders(res, req);
    res.statusCode = 204;
    return res.end();
  }

  try {
    if (req.method === 'GET') {
      const query = querystring.parse((req.url || '').split('?')[1] || '');
      const a = await authOrder(query.ref, query.token);
      if (a.error) return json(req, res, a.error.status, a.error.body);
      const mod = canSelfModify(pickupDateTime(a.order));
      return json(req, res, 200, {
        ok: true,
        order: publicView(a.order),
        self_modify: { allowed: mod.allowed, reason: mod.reason || null, hours_left: mod.hoursLeft != null ? Math.round(mod.hoursLeft) : null }
      });
    }

    if (req.method === 'PATCH' || req.method === 'POST') {
      let body = {};
      const raw = await getBody(req);
      if (raw) {
        try { body = JSON.parse(raw); }
        catch (e) { body = querystring.parse(raw); }
      }
      const a = await authOrder(body.ref, body.token);
      if (a.error) return json(req, res, a.error.status, a.error.body);
      const order = a.order;

      // 只允许特定状态的自助改期
      if (['cancelled', 'completed', 'no_show', 'in_service'].includes(order.status)) {
        return json(req, res, 409, { error: `order is ${order.status}, cannot self-modify` });
      }

      const mod = canSelfModify(pickupDateTime(order));
      if (!mod.allowed) {
        return json(req, res, 409, {
          error: 'within 48 hours of pickup, please contact support',
          reason: mod.reason,
          support: 'WhatsApp +86-155-2777-1775'
        });
      }

      const nd = String(body.pickup_date || '').trim();
      const nt = String(body.pickup_time || '').trim();
      if (!nd && !nt) return json(req, res, 400, { error: 'nothing to update' });
      if (nd && !/^\d{4}-\d{2}-\d{2}$/.test(nd)) return json(req, res, 400, { error: 'bad pickup_date' });
      if (nt && !/^\d{1,2}:\d{2}$/.test(nt)) return json(req, res, 400, { error: 'bad pickup_time' });

      // 新时间也必须仍在 48 小时之外
      const newDt = `${nd || order.pickup_date}T${String(nt || order.pickup_time || '00:00').padStart(5, '0')}:00+08:00`;
      const modNew = canSelfModify(newDt);
      if (!modNew.allowed) {
        return json(req, res, 400, { error: 'new pickup time is within 48 hours from now' });
      }

      const patch = {};
      if (nd && nd !== order.pickup_date) patch.pickup_date = nd;
      if (nt && nt !== order.pickup_time) patch.pickup_time = nt;
      if (Object.keys(patch).length === 0) {
        return json(req, res, 200, { ok: true, unchanged: true, order: publicView(order) });
      }

      const up = await updateOrder(order.ref, patch);
      if (!up.ok) return json(req, res, 500, { error: 'update failed', detail: up.error });
      if (!up.order) return json(req, res, 404, { error: 'order not found after update' });
      return json(req, res, 200, { ok: true, order: publicView(up.order) });
    }

    setCorsHeaders(res, req);
    res.statusCode = 405;
    return res.end('Method Not Allowed');
  } catch (err) {
    console.error('Chinawheely order api error:', err && err.message);
    setCorsHeaders(res, req);
    res.statusCode = 500;
    return res.end(JSON.stringify({ error: 'internal error' }));
  }
};

// Chinawheely P5 — 流量分析统计（后台）
// GET /api/analytics-stats?event=<name>&limit=100
//
// 返回：
//   {
//     stats: { today: {page_view, booking_submit, contact_submit, total}, sessions7d, byEvent: {...} },
//     rows: [ {ts, event, city, path, referrer, session_id} ]
//   }
//
// 必须鉴权：Authorization: Bearer <session token>，且邮箱需在 cw_admins 白名单内。
// 未授权一律 401（与 api/admin/leads.js 保持一致）。

const querystring = require('querystring');
const { select } = require('./_lib/db');
const { requireAdmin } = require('./_lib/auth');

const TABLE = 'cw_analytics';
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim()).filter(Boolean);

const EVENTS = [
  'page_view',
  'booking_start',
  'booking_submit',
  'booking_error',
  'contact_submit',
  'quote_request',
  'whatsapp_click',
  'phone_click',
  'city_card_click',
  'price_cta_click',
  'nav_click'
];

function setCorsHeaders(res, req) {
  const requestOrigin = req.headers.origin || req.headers.referer || '';
  let origin = '*';
  if (!ALLOWED_ORIGINS.includes('*')) {
    origin = ALLOWED_ORIGINS.includes(requestOrigin) ? requestOrigin : ALLOWED_ORIGINS[0];
  }
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Vary', 'Origin');
}
function json(req, res, status, obj) {
  setCorsHeaders(res, req);
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  return res.end(JSON.stringify(obj));
}

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') {
    setCorsHeaders(res, req);
    res.statusCode = 204;
    return res.end();
  }

  if (req.method !== 'GET') {
    setCorsHeaders(res, req);
    res.statusCode = 405;
    return res.end('Method Not Allowed');
  }

  const auth = await requireAdmin(req);
  if (!auth.ok) {
    return json(req, res, auth.status, { error: auth.error });
  }

  const query = querystring.parse((req.url || '').split('?')[1] || '');
  const event = String(query.event || '').trim();
  const limit = Math.min(Number(query.limit) || 50, 200);

  const filters = [];
  if (event && event !== 'all') filters.push(`event=eq.${encodeURIComponent(event)}`);
  const listQuery = `select=ts,event,city,path,referrer,session_id${filters.length ? '&' + filters.join('&') : ''}&order=ts.desc`;
  const listRes = await select(TABLE, listQuery, limit);

  if (!listRes.ok) {
    // 表还没建 → 前台/后台都能看到明确提示，而不是崩
    return json(req, res, 200, { error: 'query failed', detail: listRes.error, stats: null, rows: [], events: EVENTS });
  }

  // ---- 汇总统计（独立于事件筛选，保证口径一致）----
  // 「今日」按站点所在时区（Asia/Shanghai，UTC+8）切天：
  // 先把当前时刻平移到 UTC+8 得到上海本地时间，再取本地零点的真实 UTC 时刻。
  const SHANGHAI_OFFSET_MIN = 8 * 60;
  const nowMs = Date.now();
  const shifted = new Date(nowMs + SHANGHAI_OFFSET_MIN * 60000);
  const todayStart = new Date(
    Date.UTC(shifted.getUTCFullYear(), shifted.getUTCMonth(), shifted.getUTCDate())
    - SHANGHAI_OFFSET_MIN * 60000
  ).toISOString();
  const sevenDaysAgo = new Date(nowMs - 7 * 24 * 60 * 60 * 1000).toISOString();

  const dayRes = await select(TABLE, 'select=ts,event,session_id&ts=gte.' + encodeURIComponent(todayStart), 10000);
  const weekRes = await select(TABLE, 'select=session_id&ts=gte.' + encodeURIComponent(sevenDaysAgo), 20000);

  const stats = {
    today: { page_view: 0, booking_submit: 0, contact_submit: 0, total: 0 },
    sessions7d: 0,
    byEvent: {},
    // 数据量超过单次拉取上限时置 true（数字为下限估算）
    capped: false
  };

  if (dayRes.ok) {
    const sessions = new Set();
    for (const row of dayRes.rows) {
      stats.today.total += 1;
      stats.byEvent[row.event] = (stats.byEvent[row.event] || 0) + 1;
      if (row.event === 'page_view') stats.today.page_view += 1;
      else if (row.event === 'booking_submit') stats.today.booking_submit += 1;
      else if (row.event === 'contact_submit') stats.today.contact_submit += 1;
      if (row.session_id) sessions.add(row.session_id);
    }
    if (dayRes.rows.length >= 10000) stats.capped = true;
  }

  if (weekRes.ok) {
    const sessions = new Set();
    for (const row of weekRes.rows) {
      if (row.session_id) sessions.add(row.session_id);
    }
    stats.sessions7d = sessions.size;
    if (weekRes.rows.length >= 20000) stats.capped = true;
  }

  return json(req, res, 200, { stats, rows: listRes.rows, count: listRes.rows.length, events: EVENTS });
};

/**
 * POST /api/quote — 实时报价（给 booking.html 用）
 *
 * 请求体(JSON 或 form-urlencoded):
 *   city, product, vehicle, tier, extraMinutes, extraKm, pax
 *
 * 响应:
 *   { ok, currency, lines[], total, usd, usdRate, warnings[], ... }
 *   失败时 { ok:false, error, quoteRequired:true }  → 前端切换为询价模式
 */
const { quote, cityOptions, listPricedCities, lowestPrice } = require('./_lib/pricing');

// 报价接口独立限流（不占用下单提交的名额）
const QUOTE_LIMIT = Number(process.env.QUOTE_RATE_LIMIT_PER_MINUTE || 60);
const quoteBuckets = new Map();

function quoteRateLimited(ip) {
  if (!ip) return false;
  const now = Date.now();
  const b = quoteBuckets.get(ip);
  if (!b || now > b.resetAt) {
    quoteBuckets.set(ip, { count: 1, resetAt: now + 60000 });
    if (quoteBuckets.size > 5000) quoteBuckets.clear();
    return false;
  }
  b.count += 1;
  return b.count > QUOTE_LIMIT;
}

function getBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', c => { body += c.toString(); if (body.length > 1e6) { reject(new Error('too large')); req.destroy(); } });
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

function parseBody(raw, contentType) {
  const ct = String(contentType || '');
  if (ct.includes('application/json')) {
    try { return JSON.parse(raw || '{}'); } catch (e) { return {}; }
  }
  const out = {};
  String(raw || '').split('&').forEach(pair => {
    if (!pair) return;
    const i = pair.indexOf('=');
    const rawKey = i < 0 ? pair : pair.slice(0, i);
    const rawVal = i < 0 ? '' : pair.slice(i + 1);
    const k = decodeURIComponent(rawKey.replace(/\+/g, ' '));
    const v = decodeURIComponent(rawVal.replace(/\+/g, ' '));
    if (k) out[k] = v;
  });
  return out;
}

module.exports = async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(204).end();
  }
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST, OPTIONS');
    return res.status(405).json({ ok: false, error: 'METHOD_NOT_ALLOWED' });
  }

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'no-store');

  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() ||
    (req.socket && req.socket.remoteAddress) || '';
  if (quoteRateLimited(ip)) {
    return res.status(429).json({ ok: false, error: 'RATE_LIMITED' });
  }

  let data;
  try {
    data = parseBody(await getBody(req), req.headers['content-type']);
  } catch (e) {
    return res.status(400).json({ ok: false, error: 'BAD_REQUEST' });
  }

  try {
    // 元数据查询
    if (data.action === 'options') {
      const opts = cityOptions(data.city);
      if (!opts) return res.status(200).json({ ok: false, error: 'CITY_NOT_PRICED', quoteRequired: true });
      return res.status(200).json({ ok: true, ...opts });
    }
    if (data.action === 'cities') {
      return res.status(200).json({ ok: true, cities: listPricedCities() });
    }
    if (data.action === 'lowest') {
      return res.status(200).json({ ok: true, lowest: lowestPrice(data.city, data.product || 'airport') });
    }

    const result = quote(data);
    if (!result.ok) {
      return res.status(200).json(result);
    }
    return res.status(200).json(result);
  } catch (e) {
    return res.status(500).json({
      ok: false,
      error: 'QUOTE_ERROR',
      message: 'Unable to calculate price right now',
    });
  }
};

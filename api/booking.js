const querystring = require('querystring');
const { parseRequestBody } = require('./_lib/body');
const { mailerConfigured, sendMail } = require('./_lib/mailer');
const { createLead, markMail } = require('./_lib/leads');
const { buildLeadRecord, clientIp } = require('./_lib/fields');
const { isRateLimited, filledTooFast } = require('./_lib/guard');
const pricing = require('./_lib/pricing');
const { createOrder, getOrderByRef, updateOrder, generateManageToken, sha256, canSelfModify } = require('./_lib/orders');

const RECIPIENT_EMAIL = process.env.RECIPIENT_EMAIL || '15527771775@qq.com';
const SUCCESS_URL = process.env.SUCCESS_URL || 'https://www.chinawheely.com/thank-you.html';
const BOOKING_URL = process.env.BOOKING_URL || 'https://www.chinawheely.com/booking.html';
const REPLY_TO_FIELD = process.env.REPLY_TO_FIELD || 'email';
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim()).filter(Boolean);

/**
 * 表单里同名字段重复提交时（hidden + radio 共用 name），querystring.parse 会返回数组。
 * 这里统一压成第一个非空标量，避免 pricing 收到 ['airport','airport'] 而报 UNKNOWN_PRODUCT。
 */
function first(v) {
  if (Array.isArray(v)) {
    for (const x of v) {
      if (x !== undefined && x !== null && String(x).trim() !== '') return String(x).trim();
    }
    return '';
  }
  if (v === undefined || v === null) return '';
  return String(v).trim();
}

// 距离档 → 超出免费里程的估算公里数（闭区间取中位；'80+' 取下限 80，最保守）
const DISTANCE_BAND_KM = { '0-35': 17.5, '35-50': 42.5, '50-80': 65, '80+': 80 };
function extraKmFromBand(band, includedKm) {
  const mid = DISTANCE_BAND_KM[String(band || '').trim()];
  if (mid == null) return 0;
  const inc = Number(includedKm) || 0;
  return Math.max(0, Math.round(mid - inc));
}

const serviceLabels = {
  'airport': 'Airport Transfer',
  'city': 'Hourly Charter',
  'intercity': 'Intercity Transfer',
  'charter': 'Hourly Charter',
  'hourly': 'Hourly Charter',
  'airport-transfer': 'Airport Transfer',
  'intercity-transfer': 'Intercity Transfer',
  'hourly-charter': 'Hourly Charter',
  'point-to-point': 'Point-to-Point',
  'disposal': 'Disposal'
};

const vehicleLabels = {
  'economy': 'Economy Sedan',
  'business': 'Business Sedan',
  'mpv': 'MPV / Van',
  'luxury': 'Luxury Vehicle',
  'sedan_economy': '4座 经济型专车 / 4-seat Economy Sedan',
  'sedan_comfort': '4座 舒适型专车 / 4-seat Comfort Sedan',
  'sedan_4': '4座 专车 / 4-seat Sedan',
  'mpv_6': '6座 商务车 / 6-seat MPV',
  'van_8_11': '8-11座 商务车 / 8-11-seat Minivan',
  'van_12_18': '12-18座 商务车 / 12-18-seat Van',
  'coach_19_55': '19-55座 大巴 / 19-55-seat Coach'
};

/**
 * 服务端算价（权威值）
 * 前端传来的 price 一律不采信；用 pricing 引擎重算。
 * 返回 { ok, quote, priced } —— priced=false 表示该组合无公开价（转询价）。
 */
function computePrice(data) {
  try {
    const opts = {
      city: data.city,
      product: data.product || data.serviceType || 'airport',
      vehicle: data.vehicle,
      tier: data.tier,
      extraMinutes: data.extraMinutes,
      extraKm: data.extraKm,
      pax: data.passengers,
      bags: data.luggage
    };
    let q = pricing.quote(opts);
    // 用户没填额外里程、但选了距离档时，按该车型的免费里程自动折算超里程费
    // （否则「距离」是必填项却完全不影响价格，80km 接送会和 20km 同价）
    if (q.ok && !Number(opts.extraKm) && data.distanceRange) {
      const derived = extraKmFromBand(data.distanceRange, q.includedKm);
      if (derived > 0) {
        const q2 = pricing.quote(Object.assign({}, opts, { extraKm: derived }));
        if (q2.ok) q = q2;
      }
    }
    if (q.ok) return { ok: true, quote: q, priced: true };
    return { ok: false, quote: q, priced: false, reason: q.error };
  } catch (e) {
    return { ok: false, priced: false, reason: 'PRICING_ERROR', message: e && e.message };
  }
}

function getOrigin(req) {
  const requestOrigin = req.headers.origin || req.headers.referer || '';
  if (ALLOWED_ORIGINS.includes('*')) return '*';
  if (ALLOWED_ORIGINS.includes(requestOrigin)) return requestOrigin;
  return ALLOWED_ORIGINS[0] || '*';
}

function setCorsHeaders(res, req) {
  res.setHeader('Access-Control-Allow-Origin', getOrigin(req));
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Vary', 'Origin');
}

/** 出错时把用户送回预定页并带上可读原因，而不是丢一个纯文本 400 页面 */
function redirectToBooking(res, req, code, message) {
  setCorsHeaders(res, req);
  // 前端用 fetch 提交时（Accept: application/json）返回 JSON，而不是 302
  if (wantsJson(req)) {
    res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
    return res.end(JSON.stringify({ ok: false, error: code, message: message || '' }));
  }
  let url = BOOKING_URL + (BOOKING_URL.includes('?') ? '&' : '?') + 'error=' + encodeURIComponent(code);
  if (message) url += '&msg=' + encodeURIComponent(message);
  res.writeHead(302, { Location: url });
  return res.end();
}

/** 前端是否用 fetch 提交（要 JSON 响应而不是 302） */
function wantsJson(req) {
  const a = String((req && req.headers && req.headers.accept) || '').toLowerCase();
  return a.indexOf('application/json') !== -1;
}

/**
 * 成功响应。
 * - 普通表单提交 → 302 跳感谢页（保持旧行为，老缓存页也能用）
 * - fetch 提交 → 200 JSON（先建单、再展示付款码的新流程用）
 */
function respondOk(res, req, info) {
  setCorsHeaders(res, req);
  const orderRef = info.orderRef;
  const quoted = info.quoted;
  const manageToken = info.manageToken || null;
  const loc = orderRef
    ? `${SUCCESS_URL}${SUCCESS_URL.includes('?') ? '&' : '?'}ref=${encodeURIComponent(orderRef)}` +
      (quoted && quoted.total ? `&amount=${encodeURIComponent(String(quoted.total))}` : '') +
      // 自助管理 token 直接带上：邮件通道万一发不出去，客户在感谢页仍能改期/查单
      (manageToken ? `&token=${encodeURIComponent(manageToken)}` : '')
    : SUCCESS_URL;
  if (wantsJson(req)) {
    const payload = {
      ok: true,
      ref: orderRef || null,
      amountCny: quoted ? quoted.total : null,
      amountUsd: quoted ? quoted.usd : null,
      city: quoted ? quoted.city : ((info.data && (info.data.cityLabel || info.data.city)) || ''),
      vehicle: quoted ? quoted.vehicleName : ((info.data && info.data.vehicleLabel) || ''),
      redirect: loc,
      manageUrl: manageToken
        ? `${SUCCESS_URL.replace(/thank-you\.html.*$/i, '').replace(/\/+$/, '')}/manage-order.html?ref=${encodeURIComponent(orderRef || '')}&token=${encodeURIComponent(manageToken)}`
        : null
    };
    if (info.mailWarning) payload.mailWarning = info.mailWarning;
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    return res.end(JSON.stringify(payload));
  }
  res.writeHead(302, { Location: loc });
  return res.end();
}

function getBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => body += chunk.toString());
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

// P4 - 产品类型英文标签（客户邮件用）
function productLabelOf(p) {
  const map = {
    airport: 'Airport Transfer',
    charter: 'Hourly Charter',
    intercity: 'Intercity Transfer'
  };
  return map[String(p || '').toLowerCase()] || null;
}

function escapeHtml(text) {
  return String(text)
    .replace(/\u0026/g, '\u0026amp;')
    .replace(/\u003c/g, '\u0026lt;')
    .replace(/\u003e/g, '\u0026gt;')
    .replace(/"/g, '\u0026quot;')
    .replace(/'/g, '\u0026#039;');
}

function formatLabel(key) {
  return String(key)
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email).trim());
}

function getSubmitterName(data) {
  const first = data.firstName || '';
  const last = data.lastName || '';
  return `${first} ${last}`.trim();
}

/** 用服务端算出的结果重建行程摘要 */
function buildRouteSummary(data, quoted) {
  const parts = [];
  const city = quoted ? quoted.city : (data.cityLabel || data.city || '');
  if (city) parts.push(city);

  const product = quoted ? quoted.product : (data.product || data.serviceType || 'airport');
  if (product === 'airport' || product === 'intercity') {
    if (data.airport) parts.push(data.airport);
    if (data.transferDirection === 'airport-to-hotel') parts.push('→ Hotel');
    if (data.transferDirection === 'hotel-to-airport') parts.push('Hotel →');
    if (data.hotelAddress) parts.push(data.hotelAddress);
  } else if (product === 'charter') {
    if (data.charterRoute) parts.push(data.charterRoute);
    if (quoted && quoted.tierName) parts.push(quoted.tierName);
  } else {
    if (data.fromCity) parts.push(data.fromCity);
    if (data.toCity) parts.push('→ ' + data.toCity);
  }
  return parts.join(' ');
}

function buildSubject(data) {
  const parts = [];
  const serviceLabel = (data.serviceTypeLabel && String(data.serviceTypeLabel).trim()) ||
                       serviceLabels[data.serviceType] ||
                       formatLabel(data.serviceType) ||
                       '';
  if (serviceLabel) parts.push(serviceLabel);
  if (data.routeSummary && String(data.routeSummary).trim()) parts.push(String(data.routeSummary).trim());
  const name = getSubmitterName(data);
  if (name) parts.push(`from ${name}`);
  if (parts.length === 0) return 'New Chinawheely Booking';
  return `${parts.join(' ')} - Chinawheely`;
}

function buildEmail(data, meta = {}) {
  const hidden = new Set(['website', '_honey', '_subject', '_next', '_template', '_captcha', '_replyto', '_cc',
    'quoteTotalCny', 'quoteTotalUsd', 'quoteBreakdown', 'formPrice', 'formRouteSummary',
    'formServiceType', 'formVehicleLabel', 'formProduct', 'formVehicleKey', 'formTierKey',
    'formExtraMinutes', 'formExtraKm']);
  const entries = Object.entries(data).filter(([k, v]) => {
    if (hidden.has(k)) return false;
    if (v === undefined || v === null) return false;
    if (Array.isArray(v)) return v.length > 0;
    if (typeof v === 'string' && v.trim() === '') return false;
    return true;
  });

  const importantFields = new Set(['routeSummary', 'serviceTypeLabel', 'price', 'totalPrice', 'vehicleLabel', 'date', 'time', 'pickupDate', 'pickupTime', 'city', 'product', 'vehicle', 'tier']);

  const rows = entries.map(([k, v]) => {
    const label = formatLabel(k);
    const value = Array.isArray(v) ? v.join(', ') : String(v);
    const important = importantFields.has(k) ? 'background:#E8F5E9;font-weight:600;' : '';
    return `<tr style="${important}"><td style="padding:8px 12px;border:1px solid #ddd;background:${important ? '#E8F5E9' : '#f8f8f8'}"><strong>${escapeHtml(label)}</strong></td><td style="padding:8px 12px;border:1px solid #ddd;${important}">${escapeHtml(value)}</td></tr>`;
  }).join('');

  const metaRows = [];
  if (meta.orderRef) {
    metaRows.push(`<tr><td style="padding:8px 12px;border:1px solid #ddd;background:#E8F5E9"><strong>Order Number</strong></td><td style="padding:8px 12px;border:1px solid #ddd;font-weight:700">${escapeHtml(meta.orderRef)}</td></tr>`);
  }
  if (meta.reference) {
    metaRows.push(`<tr><td style="padding:8px 12px;border:1px solid #ddd;background:#f8f8f8"><strong>Booking Reference</strong></td><td style="padding:8px 12px;border:1px solid #ddd">${escapeHtml(meta.reference)}</td></tr>`);
  }
  if (meta.submittedAt) {
    metaRows.push(`<tr><td style="padding:8px 12px;border:1px solid #ddd;background:#f8f8f8"><strong>Submitted At</strong></td><td style="padding:8px 12px;border:1px solid #ddd">${escapeHtml(meta.submittedAt)}</td></tr>`);
  }
  if (meta.submitterIP) {
    metaRows.push(`<tr><td style="padding:8px 12px;border:1px solid #ddd;background:#f8f8f8"><strong>Submitter IP</strong></td><td style="padding:8px 12px;border:1px solid #ddd">${escapeHtml(meta.submitterIP)}</td></tr>`);
  }

  // 报价明细（服务端算出）
  let quoteBlock = '';
  let quotePlain = '';
  if (data.quoteJson) {
    try {
      const q = JSON.parse(data.quoteJson);
      const qrows = (q.lines || []).map(l =>
        `<tr><td style="padding:6px 12px;border:1px solid #ddd">${escapeHtml(l.label)}</td><td style="padding:6px 12px;border:1px solid #ddd;text-align:right">¥${escapeHtml(String(l.amount))}</td></tr>`
      ).join('');
      quoteBlock = `<h3 style="color:#1B4D3E;margin:18px 0 8px">Server-Calculated Price</h3>
<table style="border-collapse:collapse;width:100%;max-width:600px">
${qrows}
<tr style="background:#E8F5E9;font-weight:700"><td style="padding:8px 12px;border:1px solid #ddd">Total</td><td style="padding:8px 12px;border:1px solid #ddd;text-align:right">¥${escapeHtml(String(q.total))} CNY</td></tr>
<tr><td style="padding:6px 12px;border:1px solid #ddd">USD reference</td><td style="padding:6px 12px;border:1px solid #ddd;text-align:right">≈ $${escapeHtml(String(q.usd))} @ ${escapeHtml(String(q.usdRate))}</td></tr>
</table>`;
      quotePlain = '\nServer-Calculated Price:\n' +
        (q.lines || []).map(l => `  ${l.label}: ¥${l.amount}`).join('\n') +
        `\n  Total: ¥${q.total} CNY (≈ $${q.usd} @ ${q.usdRate})`;
    } catch (e) { /* ignore */ }
  } else if (data.pricingStatus === 'quote_requested') {
    quoteBlock = `<p style="color:#b45309">This combination has no published price — the customer is requesting a quote. Our team will respond within 2 hours.</p>`;
    quotePlain = '\nNo published price for this combination — quote request pending.';
  }

  const html = `<h2 style="color:#1B4D3E">New Chinawheely Booking Request</h2>
<p style="color:#555">Order Number: <strong>${escapeHtml(meta.orderRef || meta.reference || 'N/A')}</strong></p>
<table style="border-collapse:collapse;width:100%;max-width:600px">${metaRows.join('')}${rows}</table>
${quoteBlock}`;

  const plainMeta = [
    meta.submittedAt ? `Submitted At: ${meta.submittedAt}` : '',
    meta.submitterIP ? `Submitter IP: ${meta.submitterIP}` : ''
  ].filter(Boolean).join('\n');

  const plain = ['New Chinawheely Booking Request',
    `Order Number: ${meta.orderRef || meta.reference || 'N/A'}`, plainMeta, '']
    .filter(Boolean)
    .concat(entries.map(([k, v]) => {
      const label = formatLabel(k);
      const value = Array.isArray(v) ? v.join(', ') : String(v);
      return `${label}: ${value}`;
    }))
    .concat(quotePlain ? [quotePlain] : [])
    .join('\n');
  return { html, plain };
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

  const body = await getBody(req);
  if (body.length > 100 * 1024) {
    setCorsHeaders(res, req);
    res.statusCode = 413;
    return res.end('Payload too large');
  }

  // 前端可能发 urlencoded（传统表单）或 multipart（fetch + FormData），两种都支持
  const raw = parseRequestBody(body, req.headers['content-type']);
  // 同名字段重复提交（hidden + radio 共用 name）会让 querystring 返回数组 —— 统一压成单值
  const data = {};
  for (const key of Object.keys(raw)) {
    if (key === 'extras') {
      data.extras = Array.isArray(raw[key]) ? raw[key].filter(Boolean) : (raw[key] ? [raw[key]] : []);
      continue;
    }
    data[key] = first(raw[key]);
  }
  if (!data.product) data.product = data.serviceType || 'airport';
  if (!data.serviceType) data.serviceType = data.product;
  // 「其他城市」模式下机场是自由文本填写
  if (!data.airport && data.airportFreeText) data.airport = data.airportFreeText;
  // 没有公开价的城市：CTA 参数带来的城市名落到询价单里
  if (data.city === 'other' && data.requestedCity) data.cityLabel = data.requestedCity;

  // Honeypot: silently succeed if filled
  if ((data.website && String(data.website).trim()) || (data._honey && String(data._honey).trim())) {
    setCorsHeaders(res, req);
    res.writeHead(302, { Location: SUCCESS_URL });
    return res.end();
  }

  // P1 - 频率限制（同一 IP 每分钟最多 5 次）
  const ip = clientIp(req);
  const rl = await isRateLimited(ip);
  if (rl.limited) {
    setCorsHeaders(res, req);
    res.statusCode = 429;
    return res.end('Too many submissions. Please try again later.');
  }

  // P1 - 填写时长异常（脚本机器人），静默成功但不落库
  if (filledTooFast(data)) {
    setCorsHeaders(res, req);
    res.writeHead(302, { Location: SUCCESS_URL });
    return res.end();
  }

  const required = ['firstName', 'lastName', 'email', 'phone'];
  for (const field of required) {
    if (!data[field] || String(data[field]).trim() === '') {
      return redirectToBooking(res, req, 'missing_' + field, 'Please complete the ' + field + ' field.');
    }
  }

  if (!isValidEmail(data.email)) {
    return redirectToBooking(res, req, 'invalid_email', 'Please enter a valid email address.');
  }

  // 出发日期必须是今天或之后
  if (data.date) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(data.date)) {
      return redirectToBooking(res, req, 'invalid_date', 'Please pick a valid pick-up date.');
    }
    const now = new Date();
    const todayStr = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
    if (data.date < todayStr) {
      return redirectToBooking(res, req, 'past_date', 'The pick-up date cannot be in the past.');
    }
  }

  // ===== 服务端算价（权威值）：不采信前端传来的 price =====
  const priceResult = computePrice(data);
  const quoted = priceResult.priced && priceResult.quote;
  if (quoted) {
    data.price = '¥' + quoted.total + ' CNY';
    data.totalPrice = String(quoted.total);
    data.vehicleLabel = quoted.vehicleName;
    data.serviceTypeLabel = quoted.productLabel;
    data.routeSummary = buildRouteSummary(data, quoted);
  } else {
    // 无公开价组合 → 询价
    data.price = 'Quote on request';
    data.totalPrice = '';
    delete data.quoteTotalCny;
    delete data.quoteTotalUsd;
    delete data.quoteBreakdown;
    if (!data.vehicleLabel && data.vehicle) {
      data.vehicleLabel = vehicleLabels[data.vehicle] || data.vehicle;
    }
    if (!data.serviceTypeLabel) {
      data.serviceTypeLabel = serviceLabels[data.serviceType] || formatLabel(data.serviceType) || '';
    }
    data.routeSummary = buildRouteSummary(data, null);
  }
  data.pricingStatus = quoted ? 'priced' : 'quote_requested';
  data.quoteJson = quoted ? JSON.stringify({
    total: quoted.total,
    usd: quoted.usd,
    usdRate: quoted.usdRate,
    lines: quoted.lines,
    city: quoted.city,
    product: quoted.product,
    vehicle: quoted.vehicle,
    tier: quoted.tier,
    includedKm: quoted.includedKm,
    warnings: quoted.warnings
  }) : '';

  if (!mailerConfigured()) {
    // 注意：此时 lead / order 都还没创建，不能引用后面才声明的 reference（TDZ ReferenceError）
    return redirectToBooking(res, req, 'mail_unavailable',
      'Booking service is temporarily unavailable. Please try again shortly, or message us on WhatsApp +86 155 2777 1775.');
  }

  const submitterIP = req.headers['x-forwarded-for'] || (req.socket && req.socket.remoteAddress) || '';
  const submittedAt = new Date().toLocaleString('en-US', { timeZone: 'Asia/Shanghai', timeZoneName: 'short' });

  // P1 - 先落库：即使邮件发送失败，线索也不会丢
  const lead = await createLead(buildLeadRecord(data, 'booking', req));
  const reference = lead.ref;
  if (!lead.ok) {
    console.error('Chinawheely booking lead insert failed:', lead.error);
  }

  // P4 - 创建订单（订单号 + 状态机）
  let orderRef = null;
  let manageToken = null;
  try {
    const order = await createOrder({
      email: data.email,
      phone: data.phone,
      customerName: [data.firstName, data.lastName].filter(Boolean).join(' '),
      city: quoted ? quoted.city : (data.cityLabel || data.city || null),
      product: quoted ? quoted.product : (data.product || data.serviceType || null),
      vehicle: quoted ? quoted.vehicle : (data.vehicle || null),
      tier: quoted ? quoted.tier : (data.tier || null),
      quote: quoted ? {
        total: quoted.total, usd: quoted.usd, usdRate: quoted.usdRate,
        lines: quoted.lines, includedKm: quoted.includedKm, warnings: quoted.warnings
      } : null,
      trip: {
        date: data.date, time: data.time,
        pax: data.passengers, luggage: data.luggage
      },
      contact: {
        airport: data.airport, transferDirection: data.transferDirection,
        hotelAddress: data.hotelAddress, charterRoute: data.charterRoute,
        fromCity: data.fromCity, toCity: data.toCity,
        flightNumber: data.flightNumber, airline: data.airline,
        extras: data.extras
      },
      notes: data.notes,
      payment: { method: data.paymentMethod }
    });
    if (order.ok) {
      orderRef = order.ref;
      manageToken = order.manageToken;
    } else {
      console.error('Chinawheely order create failed:', order.error);
    }
  } catch (e) {
    console.error('Chinawheely order create error:', e && e.message);
  }

  const baseSubject = buildSubject(data);
  const subject = (reference || orderRef) ? `${baseSubject} [${orderRef || reference}]` : baseSubject;

  // ⚠ 订单没入库就不能让客户以为提交成功（否则后台看不到这单）
  if (!orderRef) {
    console.error('Chinawheely order not created (no ref)');
    setCorsHeaders(res, req);
    if (wantsJson(req)) {
      res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({
        ok: false, error: 'order_create_failed',
        message: 'We could not create your booking. Please try again, or message us on WhatsApp +86 155 2777 1775.'
      }));
    }
    return redirectToBooking(res, req, 'order_create_failed', 'Please try again or contact us on WhatsApp +86 155 2777 1775');
  }
  const { html, plain } = buildEmail(data, {
    reference: reference || orderRef,
    orderRef,
    manageToken,
    submittedAt,
    submitterIP
  });

  const replyEmail = data[REPLY_TO_FIELD] && String(data[REPLY_TO_FIELD]).trim();

  // 邮件改为并行发送，且**不阻塞响应**：
  // 旧写法是「客户邮件 → 通知邮件」串行 await 再响应，实测要 8～10 秒，
  // 客户盯着「Creating your order…」会以为卡死而重复提交。
  // 现在：订单入库后立即返回（1 秒内），邮件在响应后补齐。
  const mailTasks = [];

  // P4 - 客户确认邮件（含订单号 + 自助管理链接）；失败不阻断主流程
  try {
    if (data.email && orderRef) {
      const siteBase = SUCCESS_URL.replace(/thank-you\.html.*$/i, '').replace(/\/+$/, '') || 'https://www.chinawheely.com';
      const manageUrl = `${siteBase}/manage-order.html?ref=${encodeURIComponent(orderRef)}&token=${encodeURIComponent(manageToken)}`;
      const q = quoted || {};
      const priceLine = quoted
        ? `<p style="font-size:18px"><strong>¥${q.total} CNY</strong> <span style=\"color:#64748b\">(≈ $${q.usd} USD)</span></p>`
        : `<p><strong>Price:</strong> We'll send you a confirmed quote within 2 hours.</p>`;
      const custHtml = `<div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:600px;margin:0 auto;color:#1f2937">
<h2 style="color:#1B4D3E;margin:0 0 4px">Booking received — ${escapeHtml(orderRef)}</h2>
<p style="color:#64748b;margin:0 0 16px">Thank you, ${escapeHtml(String(data.firstName || data.lastName || 'traveller'))}! Your booking request is confirmed and our team is reviewing it now.</p>
<table style="border-collapse:collapse;width:100%;font-size:14px">
<tr><td style="padding:6px 10px;border:1px solid #e2e8f0;background:#f8fafc;width:140px">Order Number</td><td style="padding:6px 10px;border:1px solid #e2e8f0;font-weight:700">${escapeHtml(orderRef)}</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #e2e8f0;background:#f8fafc">Service</td><td style="padding:6px 10px;border:1px solid #e2e8f0">${escapeHtml(String(q.serviceTypeLabel || productLabelOf(data.product) || 'Private car service'))}</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #e2e8f0;background:#f8fafc">City</td><td style="padding:6px 10px;border:1px solid #e2e8f0">${escapeHtml(String(q.city || data.city || ''))}</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #e2e8f0;background:#f8faff">Pickup</td><td style="padding:6px 10px;border:1px solid #e2e8f0">${escapeHtml(String(data.date || ''))} ${escapeHtml(String(data.time || ''))}</td></tr>
${q.vehicleLabel ? `<tr><td style="padding:6px 10px;border:1px solid #e2e8f0;background:#f8fafc">Vehicle</td><td style="padding:6px 10px;border:1px solid #e2e8f0">${escapeHtml(String(q.vehicleLabel))}</td></tr>` : ''}
</table>
<div style="margin:14px 0">${priceLine}</div>
<h3 style="color:#1B4D3E;font-size:15px;margin:18px 0 6px">How to pay</h3>
<p style="font-size:14px">Pay via <strong>PayPal</strong> or <strong>Alipay</strong> — scan the QR code on our <a href="${siteBase}/thank-you.html?ref=${encodeURIComponent(orderRef)}${quoted && quoted.total ? '&amount=' + encodeURIComponent(String(quoted.total)) : ''}#payment">payment page</a>${quoted && quoted.total ? ` and enter <strong>¥${quoted.total}</strong>` : ''}, then send the payment screenshot to our WhatsApp below. We confirm within 10 minutes.</p>
<h3 style="color:#1B4D3E;font-size:15px;margin:18px 0 6px">Manage your booking</h3>
<p style="font-size:14px">View details or reschedule (free up to 48 hours before pickup):<br>
<a href="${manageUrl}">${manageUrl}</a></p>
<p style="font-size:12px;color:#64748b">This link is personal — keep it safe. It is valid for 30 days.</p>
<h3 style="color:#1B4D3E;font-size:15px;margin:18px 0 6px">Need help?</h3>
<p style="font-size:14px">WhatsApp / WeChat: <strong>+86 155 2777 1775</strong> (Beijing time 8:00–24:00)<br>Email: ${escapeHtml(RECIPIENT_EMAIL)}</p>
<p style="font-size:12px;color:#94a3b8;margin-top:20px">Chinawheely · Licensed travel agency L-HUB-101603 · <a href="${siteBase}/index.html" style=\"color:#94a3b8\">www.chinawheely.com</a></p>
</div>`;
      const custPlain = [
        `Booking received — ${orderRef}`,
        `Service: ${q.serviceTypeLabel || productLabelOf(data.product) || 'Private car service'}`,
        `City: ${q.city || data.city || ''}`,
        `Pickup: ${data.date || ''} ${data.time || ''}`,
        q.vehicleLabel ? `Vehicle: ${q.vehicleLabel}` : '',
        quoted ? `Price: ¥${q.total} CNY (≈ $${q.usd} USD)` : 'Price: quote to follow within 2 hours',
        '',
        'How to pay: PayPal or Alipay QR on your payment page; send screenshot to WhatsApp +86 155 2777 1775.',
        '',
        `Manage your booking (reschedule up to 48h before pickup):`,
        manageUrl,
        '',
        `Support: WhatsApp/WeChat +86 155 2777 1775 (8:00-24:00 Beijing) · ${RECIPIENT_EMAIL}`
      ].filter(l => l !== undefined).join('\n');
      mailTasks.push(function () {
        return sendMail({
          to: String(data.email).trim(),
          subject: `Your Chinawheely booking ${orderRef}`,
          html: custHtml,
          text: custPlain,
          replyTo: RECIPIENT_EMAIL
        }).catch(function (err) {
          console.error('Chinawheely customer mail error:', err && err.message);
        });
      });
    }
  } catch (mailErr) {
    console.error('Chinawheely customer mail build error:', mailErr && mailErr.message);
  }

  mailTasks.push(function () {
    return sendMail({
      to: RECIPIENT_EMAIL,
      subject,
      html,
      text: plain,
      replyTo: replyEmail
    })
      .then(function () { return markMail(reference, 'sent'); })
      .catch(function (err) {
        console.error('Chinawheely booking mail error:', err && err.message);
        return markMail(reference, 'failed', (err && err.message) || 'unknown error');
      });
  });

  // 先把订单结果返回给客户（订单已入库），邮件并行补齐。
  // handler 的 promise 仍然 pending，函数不会提前冻结，邮件能发完。
  const respondedAt = Date.now();
  respondOk(res, req, { orderRef, quoted, data, manageToken });
  // 串行发送（不并发）：并发连 QQ SMTP 会被限速，实测并发耗时 54 秒、串行只要 8 秒
  for (const job of mailTasks) {
    await job();
  }
  console.log(`[booking] ${orderRef} mails settled ${Date.now() - respondedAt}ms after response (sent=${mailTasks.length})`);
  return;
}

// Chinawheely P1 — 表单字段归一化（contact / booking 通用）

const HONEYPOT_FIELDS = ['website', '_honey', 'robots', 'botfield'];

function str(value) {
  if (value === undefined || value === null) return '';
  return String(value).trim();
}

function firstNonEmpty(data, keys) {
  for (const k of keys) {
    const v = str(data[k]);
    if (v) return v;
  }
  return '';
}

function detectLang(text) {
  const s = String(text || '');
  const cjk = (s.match(/[\u4e00-\u9fff]/g) || []).length;
  return cjk >= 2 ? 'zh' : 'en';
}

function clientIp(req) {
  const xff = req.headers['x-forwarded-for'];
  if (xff) return String(xff).split(',')[0].trim();
  return (req.socket && req.socket.remoteAddress) || '';
}

/** 蜜罐：任一隐藏字段有值即判定为机器人 */
function isBot(data) {
  for (const f of HONEYPOT_FIELDS) {
    if (str(data[f])) return true;
  }
  return false;
}

/**
 * 生成统一线索记录
 */
function buildLeadRecord(data, source, req) {
  const name =
    firstNonEmpty(data, ['name', 'fullName']) ||
    [str(data.firstName), str(data.lastName)].filter(Boolean).join(' ');
  const email = str(data.email).toLowerCase();
  const phone = str(data.phone);
  const message = firstNonEmpty(data, ['message', 'description', 'notes', 'extras']);

  const fromCity = firstNonEmpty(data, ['fromCity', 'city', 'cityRoute', 'routeSummary']);
  const toCity = firstNonEmpty(data, ['toCity', 'hotelAddress', 'customAddress', 'airport']);
  const city = source === 'booking' ? fromCity || toCity : firstNonEmpty(data, ['city', 'fromCity']);

  const payload = {};
  for (const [k, v] of Object.entries(data || {})) {
    if (HONEYPOT_FIELDS.includes(k)) continue;
    if (v === undefined || v === null) continue;
    if (Array.isArray(v)) {
      if (v.length) payload[k] = v;
      continue;
    }
    const s = String(v).trim();
    if (s) payload[k] = s;
  }

  const sigSource = source === 'booking'
    ? [data.serviceType, data.vehicle, data.date, data.time, data.fromCity, data.toCity, data.passengers, data.price]
    : [data.subject, message.slice(0, 120)];
  payload.__sig = sigSource.map((v) => str(v)).join('|');

  const ua = str(req && req.headers && req.headers['user-agent']);

  return {
    source,
    status: 'new',
    name: name || null,
    email: email || null,
    phone: phone || null,
    city: city || null,
    subject: str(data.subject) || null,
    message: message || null,
    payload,
    ip: clientIp(req),
    ua: ua ? ua.slice(0, 300) : null,
    lang: detectLang([message, data.subject, data.description].join(' ')),
    mail_status: 'pending',
    utm_source: str(data.utm_source) || null,
    utm_medium: str(data.utm_medium) || null,
    utm_campaign: str(data.utm_campaign) || null,
    utm_content: str(data.utm_content) || null,
    utm_term: str(data.utm_term) || null
  };
}

/** 城市提取（用于展示） */
function extractCity(data) {
  return firstNonEmpty(data, ['fromCity', 'city', 'cityRoute']) || '';
}

module.exports = {
  str,
  firstNonEmpty,
  detectLang,
  clientIp,
  isBot,
  buildLeadRecord,
  extractCity,
  HONEYPOT_FIELDS
};

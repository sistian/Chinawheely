// Chinawheely P5 — 自建流量分析写入端点（替代 GA4）
// POST /api/analytics
//
// 设计要点：
//   * 前台 js/analytics.js 用 sendBeacon / fetch(keepalive) 上报，事件名与 GA4 口径一致
//   * 公开写入端点 → 必须限流（IP + 时间窗，进程内计数）
//   * 硬性隐私要求：不采 PII；props 里出现 email/phone/name/tel 等键直接剔除
//   * 表未建立（Supabase SQL 还没跑）时降级返回 204，绝不 500、绝不影响前台页面
//   * 副作用（写库）必须在响应前完成 —— Vercel 响应后会冻结函数实例
//     （见 memory/2026-11-06-chinawheely-mail-rootcause.md）

const { rest } = require('./_lib/db');
const { clientIp } = require('./_lib/fields');

const TABLE = 'cw_analytics';

// 事件白名单：与 js/analytics.js 派发的 GA4 事件名保持一致
// 主口径（11 个，与业务漏斗一一对应）：
//   page_view / booking_start / booking_submit / booking_error / contact_submit /
//   quote_request / whatsapp_click / phone_click / city_card_click / price_cta_click / nav_click
// 辅助事件（js/analytics.js 内部派发，同口径一并入库）：
//   contact_start / api_call / booking_submit_error / contact_submit_error
const PRIMARY_EVENTS = [
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
const EXTRA_EVENTS = [
  'contact_start',
  'api_call',
  'booking_submit_error',
  'contact_submit_error'
];
const ALLOWED_EVENTS = PRIMARY_EVENTS.concat(EXTRA_EVENTS);

// 长度上限
const MAX_BODY_BYTES = 4 * 1024;
const MAX_PATH = 300;
const MAX_CITY = 80;
const MAX_REFERRER = 300;
const MAX_UA = 200;
const MAX_SESSION = 64;
const MAX_PROPS_BYTES = 2000;

// PII 键名（大小写不敏感，命中即剔除整个键）
// 策略：强特征用子串匹配（email/phone/mobile/wechat/...），弱特征用整词匹配，
//       避免误伤 hotel / trip 这类正常业务词。
const PII_SUBSTRINGS = ['email', 'e_mail', 'phone', 'mobile', 'wechat', 'weixin', 'passport', 'idcard', 'id_card', 'telephone'];
const PII_EXACT = new Set([
  'tel', 'name', 'firstname', 'lastname', 'fullname', 'username', 'nickname',
  'contact', 'address', 'message', 'msg', 'note', 'notes', 'text', 'comment',
  'ip', 'ipaddress', 'userid', 'user_id', 'passportno', 'whatsapp'
]);

function isPiiKey(key) {
  const token = String(key).toLowerCase().replace(/[^a-z0-9]/g, '');
  if (!token) return true;
  if (PII_EXACT.has(token)) return true;
  // *name / *phone 之类派生词（如 firstname、servicename、user_phone）
  if (/(^|[a-z])name$/.test(token)) return true;
  if (/(^|[a-z])phones?$/.test(token)) return true;
  for (const frag of PII_SUBSTRINGS) {
    if (token.includes(frag)) return true;
  }
  return false;
}

const RATE_LIMIT_PER_MINUTE = Number(process.env.ANALYTICS_RATE_LIMIT_PER_MINUTE || 300);
const RATE_WINDOW_MS = 60 * 1000;

// 进程内限流桶：ip -> {count, resetAt}
const buckets = new Map();

function rateLimited(ip) {
  if (!ip) return false;
  const now = Date.now();
  const bucket = buckets.get(ip);
  if (!bucket || now > bucket.resetAt) {
    buckets.set(ip, { count: 1, resetAt: now + RATE_WINDOW_MS });
    if (buckets.size > 5000) buckets.clear();
    return false;
  }
  bucket.count += 1;
  return bucket.count > RATE_LIMIT_PER_MINUTE;
}

// 站点域名（含各城市子域）白名单
const SITE_ORIGIN_RE = /^https:\/\/([a-z0-9-]+\.)*chinawheely\.com$/i;

function setCorsHeaders(res, req) {
  // 公开写入端点（无凭证、无敏感返回、响应体为空）：
  // 对站点自身域名回显 Origin，避免 sendBeacon / fetch 因 CORS 校验失败在控制台报错；
  // 其它 Origin 一律返回 *（请求本身仍会送达服务端，由 IP 限流兜底）。
  const requestOrigin = String(req.headers.origin || '');
  const allow = requestOrigin && SITE_ORIGIN_RE.test(requestOrigin) ? requestOrigin : '*';
  res.setHeader('Access-Control-Allow-Origin', allow);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Vary', 'Origin');
}

function getBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    let tooLarge = false;
    req.on('data', chunk => {
      if (tooLarge) return;                 // 已超限：不再累积，但仍等待 end
      body += chunk.toString();
      if (body.length > MAX_BODY_BYTES * 4) {
        tooLarge = true;
        body = body.slice(0, MAX_BODY_BYTES * 4);
      }
    });
    req.on('end', () => resolve(tooLarge ? null : body));
    req.on('error', reject);
  });
}

function str(value) {
  if (value === undefined || value === null) return '';
  return String(value).trim();
}

function clip(value, max) {
  const s = str(value);
  return s ? s.slice(0, max) : '';
}

/** 剔除 PII 键（大小写不敏感）；只保留原始值类型友好的简单结构 */
function sanitizeProps(props) {
  if (!props || typeof props !== 'object' || Array.isArray(props)) return null;
  const out = {};
  for (const [key, value] of Object.entries(props)) {
    if (!key || isPiiKey(key)) continue;
    if (value === null || value === undefined) continue;
    if (typeof value === 'object') continue; // 不接受嵌套对象 / 数组
    const s = str(value);
    if (!s) continue;
    out[key] = s.slice(0, 200);
  }
  let serialized;
  try {
    serialized = JSON.stringify(out);
  } catch (e) {
    return null;
  }
  if (!serialized || serialized === '{}') return null;
  if (serialized.length > MAX_PROPS_BYTES) return null;
  return out;
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

  const raw = await getBody(req);
  if (raw === null || raw.length > MAX_BODY_BYTES) {
    setCorsHeaders(res, req);
    res.statusCode = 413;
    return res.end('Payload too large');
  }

  let body;
  try {
    body = JSON.parse(raw);
  } catch (e) {
    setCorsHeaders(res, req);
    res.statusCode = 400;
    return res.end('Invalid JSON');
  }

  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    setCorsHeaders(res, req);
    res.statusCode = 400;
    return res.end('Invalid body');
  }

  const event = str(body.event);
  if (!event) {
    setCorsHeaders(res, req);
    res.statusCode = 400;
    return res.end('Missing event');
  }
  if (!ALLOWED_EVENTS.includes(event)) {
    setCorsHeaders(res, req);
    res.statusCode = 400;
    return res.end('Unknown event');
  }

  const props = sanitizeProps(body.props);

  // 限流：同一 IP 每分钟最多 RATE_LIMIT_PER_MINUTE 次
  const ip = clientIp(req);
  if (rateLimited(ip)) {
    setCorsHeaders(res, req);
    res.statusCode = 429;
    return res.end('Too many requests');
  }

  const row = {
    event,
    path: clip(body.path, MAX_PATH) || null,
    city: clip(body.city, MAX_CITY) || null,
    referrer: clip(body.referrer, MAX_REFERRER) || null,
    session_id: clip(body.session_id, MAX_SESSION) || null,
    ua: clip(body.ua, MAX_UA) || null,
    props: props || null
  };

  // 副作用必须在响应前完成（Vercel 响应后冻结实例）
  const inserted = await rest(TABLE, {
    method: 'POST',
    headers: { Prefer: 'return=minimal' },
    body: row
  });
  if (!inserted.ok) {
    // 表不存在 / Supabase 未配置 → 静默降级，前台无感知
    console.error('Chinawheely analytics insert failed:', inserted.error);
    setCorsHeaders(res, req);
    res.statusCode = 204;
    return res.end();
  }

  setCorsHeaders(res, req);
  res.statusCode = 204;
  return res.end();
};

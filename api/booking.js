const querystring = require('querystring');
const { mailerConfigured, sendMail } = require('./_lib/mailer');

const RECIPIENT_EMAIL = process.env.RECIPIENT_EMAIL || '15527771775@qq.com';
const SUCCESS_URL = process.env.SUCCESS_URL || 'https://www.chinawheely.com/thank-you.html';
const REPLY_TO_FIELD = process.env.REPLY_TO_FIELD || 'email';
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim()).filter(Boolean);

const serviceLabels = {
  'airport': 'Airport Pickup',
  'city': 'City Transfer',
  'intercity': 'Intercity Transfer',
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
  'luxury': 'Luxury Vehicle'
};

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

function getBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => body += chunk.toString());
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
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
  const hidden = new Set(['website', '_honey', '_subject', '_next', '_template', '_captcha', '_replyto', '_cc']);
  const entries = Object.entries(data).filter(([k, v]) => {
    if (hidden.has(k)) return false;
    if (v === undefined || v === null) return false;
    if (Array.isArray(v)) return v.length > 0;
    if (typeof v === 'string' && v.trim() === '') return false;
    return true;
  });

  const importantFields = new Set(['routeSummary', 'serviceTypeLabel', 'price', 'totalPrice', 'vehicleLabel', 'date', 'time', 'pickupDate', 'pickupTime']);

  const rows = entries.map(([k, v]) => {
    const label = formatLabel(k);
    const value = Array.isArray(v) ? v.join(', ') : String(v);
    const important = importantFields.has(k) ? 'background:#E8F5E9;font-weight:600;' : '';
    return `<tr style="${important}"><td style="padding:8px 12px;border:1px solid #ddd;background:${important ? '#E8F5E9' : '#f8f8f8'}"><strong>${escapeHtml(label)}</strong></td><td style="padding:8px 12px;border:1px solid #ddd;${important}">${escapeHtml(value)}</td></tr>`;
  }).join('');

  const metaRows = [];
  if (meta.reference) {
    metaRows.push(`<tr><td style="padding:8px 12px;border:1px solid #ddd;background:#f8f8f8"><strong>Booking Reference</strong></td><td style="padding:8px 12px;border:1px solid #ddd">${escapeHtml(meta.reference)}</td></tr>`);
  }
  if (meta.submittedAt) {
    metaRows.push(`<tr><td style="padding:8px 12px;border:1px solid #ddd;background:#f8f8f8"><strong>Submitted At</strong></td><td style="padding:8px 12px;border:1px solid #ddd">${escapeHtml(meta.submittedAt)}</td></tr>`);
  }
  if (meta.submitterIP) {
    metaRows.push(`<tr><td style="padding:8px 12px;border:1px solid #ddd;background:#f8f8f8"><strong>Submitter IP</strong></td><td style="padding:8px 12px;border:1px solid #ddd">${escapeHtml(meta.submitterIP)}</td></tr>`);
  }

  const html = `<h2 style="color:#1B4D3E">New Chinawheely Booking Request</h2>
<p style="color:#555">Booking Reference: <strong>${escapeHtml(meta.reference || 'N/A')}</strong></p>
<table style="border-collapse:collapse;width:100%;max-width:600px">${metaRows.join('')}${rows}</table>`;

  const plainMeta = [
    meta.submittedAt ? `Submitted At: ${meta.submittedAt}` : '',
    meta.submitterIP ? `Submitter IP: ${meta.submitterIP}` : ''
  ].filter(Boolean).join('\n');

  const plain = ['New Chinawheely Booking Request', `Booking Reference: ${meta.reference || 'N/A'}`, plainMeta, '']
    .filter(Boolean)
    .concat(entries.map(([k, v]) => {
      const label = formatLabel(k);
      const value = Array.isArray(v) ? v.join(', ') : String(v);
      return `${label}: ${value}`;
    }))
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

  const data = querystring.parse(body);

  // Honeypot: silently succeed if filled
  if ((data.website && String(data.website).trim()) || (data._honey && String(data._honey).trim())) {
    setCorsHeaders(res, req);
    res.writeHead(302, { Location: SUCCESS_URL });
    return res.end();
  }

  const required = ['firstName', 'lastName', 'email', 'phone'];
  for (const field of required) {
    if (!data[field] || String(data[field]).trim() === '') {
      setCorsHeaders(res, req);
      res.statusCode = 400;
      return res.end('Missing required field: ' + field);
    }
  }

  if (!isValidEmail(data.email)) {
    setCorsHeaders(res, req);
    res.statusCode = 400;
    return res.end('Invalid email address');
  }

  if (!mailerConfigured()) {
    setCorsHeaders(res, req);
    res.statusCode = 503;
    return res.end('Mail service is not configured. Set SMTP_USER/SMTP_PASS in the Vercel dashboard.');
  }

  const submitterIP = req.headers['x-forwarded-for'] || (req.socket && req.socket.remoteAddress) || '';
  const submittedAt = new Date().toLocaleString('en-US', { timeZone: 'Asia/Shanghai', timeZoneName: 'short' });
  const reference = 'CWC-' + Date.now().toString(36).toUpperCase() + '-' + Math.floor(Math.random() * 10000).toString().padStart(4, '0');

  const baseSubject = buildSubject(data);
  const subject = reference ? `${baseSubject} [${reference}]` : baseSubject;
  const { html, plain } = buildEmail(data, { reference, submittedAt, submitterIP });

  const replyEmail = data[REPLY_TO_FIELD] && String(data[REPLY_TO_FIELD]).trim();

  try {
    await sendMail({
      to: RECIPIENT_EMAIL,
      subject,
      html,
      text: plain,
      replyTo: replyEmail
    });
    setCorsHeaders(res, req);
    res.writeHead(302, { Location: SUCCESS_URL });
    return res.end();
  } catch (err) {
    console.error('Chinawheely booking mail error:', err && err.message);
    setCorsHeaders(res, req);
    res.statusCode = 502;
    return res.end('Mail error: ' + (err && err.message ? err.message : 'unknown error'));
  }
};

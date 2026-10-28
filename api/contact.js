const querystring = require('querystring');
const { mailerConfigured, sendMail } = require('./_lib/mailer');

const RECIPIENT_EMAIL = process.env.RECIPIENT_EMAIL || '15527771775@qq.com';
const SUCCESS_URL = process.env.SUCCESS_URL || 'https://www.chinawheely.com/thank-you.html';
const REPLY_TO_FIELD = process.env.REPLY_TO_FIELD || 'email';
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim()).filter(Boolean);

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

function buildEmail(data) {
  const hidden = new Set(['website', '_honey', '_subject', '_next', '_template', '_captcha', '_replyto', '_cc']);
  const entries = Object.entries(data).filter(([k, v]) => {
    if (hidden.has(k)) return false;
    if (v === undefined || v === null) return false;
    if (Array.isArray(v)) return v.length > 0;
    if (typeof v === 'string' && v.trim() === '') return false;
    return true;
  });

  const rows = entries.map(([k, v]) => {
    const label = formatLabel(k);
    const value = Array.isArray(v) ? v.join(', ') : String(v);
    return `<tr><td style="padding:8px 12px;border:1px solid #ddd;background:#f8f8f8"><strong>${escapeHtml(label)}</strong></td><td style="padding:8px 12px;border:1px solid #ddd">${escapeHtml(value)}</td></tr>`;
  }).join('');

  const html = `<h2 style="color:#1B4D3E">New Chinawheely Contact Form Submission</h2>
<table style="border-collapse:collapse;width:100%;max-width:600px">${rows}</table>`;

  const plain = ['New Chinawheely Contact Form Submission', '']
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

  // Honeypot: silently succeed if a bot filled the hidden field
  if ((data.website && String(data.website).trim()) || (data._honey && String(data._honey).trim())) {
    setCorsHeaders(res, req);
    res.writeHead(302, { Location: SUCCESS_URL });
    return res.end();
  }

  const required = ['firstName', 'lastName', 'email', 'message'];
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

  const name = getSubmitterName(data);
  const subject = data.subject && String(data.subject).trim()
    ? `Contact: ${String(data.subject).trim()} - ${name}`
    : `New Contact Form Submission - ${name}`;
  const { html, plain } = buildEmail(data);

  const replyTo = data[REPLY_TO_FIELD] && String(data[REPLY_TO_FIELD]).trim();

  try {
    await sendMail({
      to: RECIPIENT_EMAIL,
      subject,
      html,
      text: plain,
      replyTo
    });
    setCorsHeaders(res, req);
    res.writeHead(302, { Location: SUCCESS_URL });
    return res.end();
  } catch (err) {
    console.error('Chinawheely contact mail error:', err && err.message);
    setCorsHeaders(res, req);
    res.statusCode = 502;
    return res.end('Mail error: ' + (err && err.message ? err.message : 'unknown error'));
  }
};

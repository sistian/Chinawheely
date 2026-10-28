// Chinawheely mail transport
// Primary: SMTP (QQ / Foxmail) — proven working channel for this account.
// Fallback: SendGrid API (only used when SMTP_USER/SMTP_PASS are absent).

const https = require('https');

const SMTP_HOST = process.env.SMTP_HOST || 'smtp.qq.com';
const SMTP_PORT = Number(process.env.SMTP_PORT || 465);
const SMTP_USER = process.env.SMTP_USER || '';
const SMTP_PASS = process.env.SMTP_PASS || process.env.QQ_AUTH_CODE || '';
// The From address must match the SMTP account, otherwise the server rejects it (501).
const MAIL_FROM = process.env.MAIL_FROM || SMTP_USER;
const MAIL_FROM_NAME = process.env.MAIL_FROM_NAME || 'Chinawheely';

const SENDGRID_API_KEY = process.env.SENDGRID_API_KEY || '';
const SENDGRID_FROM_EMAIL = process.env.SENDGRID_FROM_EMAIL || MAIL_FROM;

let smtpTransport = null;

function getSmtpTransport() {
  if (!SMTP_USER || !SMTP_PASS) return null;
  if (!smtpTransport) {
    // Lazy require so the function does not crash when nodemailer is not installed.
    const nodemailer = require('nodemailer');
    smtpTransport = nodemailer.createTransport({
      host: SMTP_HOST,
      port: SMTP_PORT,
      secure: SMTP_PORT === 465,
      auth: { user: SMTP_USER, pass: SMTP_PASS }
    });
  }
  return smtpTransport;
}

function mailerConfigured() {
  return !!getSmtpTransport() || !!SENDGRID_API_KEY;
}

function sendViaSendGrid({ to, subject, html, text, replyTo }) {
  const payload = {
    personalizations: [{ to: [{ email: to }] }],
    from: { email: SENDGRID_FROM_EMAIL },
    subject,
    content: [
      { type: 'text/plain', value: text },
      { type: 'text/html', value: html }
    ]
  };
  if (replyTo) payload.reply_to = { email: replyTo };

  const postData = JSON.stringify(payload);
  return new Promise((resolve, reject) => {
    const request = https.request({
      hostname: 'api.sendgrid.com',
      port: 443,
      path: '/v3/mail/send',
      method: 'POST',
      headers: {
        Authorization: 'Bearer ' + SENDGRID_API_KEY,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    }, (response) => {
      let responseBody = '';
      response.on('data', (chunk) => { responseBody += chunk; });
      response.on('end', () => {
        if (response.statusCode >= 200 && response.statusCode < 300) return resolve();
        reject(new Error('SendGrid error ' + response.statusCode + ': ' + responseBody));
      });
    });
    request.on('error', reject);
    request.write(postData);
    request.end();
  });
}

async function sendMail({ to, subject, html, text, replyTo }) {
  const transport = getSmtpTransport();
  if (transport) {
    const info = await transport.sendMail({
      from: `"${MAIL_FROM_NAME}" <${MAIL_FROM}>`,
      to,
      subject,
      html,
      text,
      replyTo: replyTo || undefined
    });
    return info;
  }
  if (SENDGRID_API_KEY) {
    return sendViaSendGrid({ to, subject, html, text, replyTo });
  }
  throw new Error('No mail transport configured (set SMTP_USER/SMTP_PASS or SENDGRID_API_KEY)');
}

module.exports = { mailerConfigured, sendMail };

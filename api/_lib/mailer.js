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

// 超时：nodemailer 默认连接超时 120 秒，Vercel 函数等不到那会儿，
// 失败时整单能拖几十秒。收紧到 15 秒，失败就快速换下一条通道。
const SMTP_TIMEOUT = {
  connectionTimeout: 15000,
  greetingTimeout: 15000,
  socketTimeout: 20000
};

function getSmtpTransport() {
  if (!SMTP_USER || !SMTP_PASS) return null;
  if (!smtpTransport) {
    // Lazy require so the function does not crash when nodemailer is not installed.
    const nodemailer = require('nodemailer');
    smtpTransport = nodemailer.createTransport({
      host: SMTP_HOST,
      port: SMTP_PORT,
      secure: SMTP_PORT === 465,
      auth: { user: SMTP_USER, pass: SMTP_PASS },
      ...SMTP_TIMEOUT
    });
  }
  return smtpTransport;
}

/** 备选通道：换端口 / 换 TLS 模式（出口 IP 被 SMTP 服务端拉黑时能救回来） */
function buildAltTransport(port, secure) {
  const nodemailer = require('nodemailer');
  return nodemailer.createTransport({
    host: SMTP_HOST,
    port: port,
    secure: secure,
    requireTLS: !secure && port !== 25,
    auth: { user: SMTP_USER, pass: SMTP_PASS },
    ...SMTP_TIMEOUT
  });
}

/** 诊断信息（不含密码）：主机、端口、TLS 模式、账号 */
function mailTarget() {
  return `${SMTP_HOST}:${SMTP_PORT} secure=${SMTP_PORT === 465} user=${SMTP_USER}`;
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
  const message = {
    from: `"${MAIL_FROM_NAME}" <${MAIL_FROM}>`,
    to,
    subject,
    html,
    text,
    replyTo: replyTo || undefined
  };

  if (SMTP_USER && SMTP_PASS) {
    // 主通道 → 换端口/TLS 模式 → 再试一次（Vercel 可能换了个出口 IP）
    const altPort = SMTP_PORT === 465 ? 587 : 465;
    const altSecure = SMTP_PORT !== 465;
    const plans = [
      { label: 'smtp-primary', transport: getSmtpTransport() },
      { label: 'smtp-alt', transport: buildAltTransport(altPort, altSecure) },
      { label: 'smtp-retry', transport: buildAltTransport(SMTP_PORT, SMTP_PORT === 465) }
    ];
    let lastErr = null;
    for (let i = 0; i < plans.length; i++) {
      const p = plans[i];
      try {
        const info = await p.transport.sendMail(message);
        console.log(`[mail] ok via ${p.label} (${mailTarget()}) -> ${to}`);
        return info;
      } catch (err) {
        lastErr = err;
        console.error(`[mail] ${p.label} failed (${mailTarget()}):`, err && err.message);
        if (i < plans.length - 1) {
          await new Promise(r => setTimeout(r, 800));
        }
      }
    }
    throw lastErr;
  }
  if (SENDGRID_API_KEY) {
    return sendViaSendGrid({ to, subject, html, text, replyTo });
  }
  throw new Error('No mail transport configured (set SMTP_USER/SMTP_PASS or SENDGRID_API_KEY)');
}

module.exports = { mailerConfigured, sendMail };

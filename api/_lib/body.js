/**
 * 请求体解析。
 *
 * 背景：网页表单（<form method="post">）发的是 application/x-www-form-urlencoded，
 * 但前端用 fetch + new FormData() 提交时发的是 multipart/form-data。
 * 之前服务端一律用 querystring.parse()，遇到 multipart 会解析出空对象，
 * 表现为「明明填了姓名邮箱，服务端却说 firstName 为空」。
 *
 * 这里按 Content-Type 分派，两种格式都支持。
 */
const querystring = require('querystring');

/** 解析 multipart/form-data，返回普通对象（同名字段以数组形式保留） */
function parseMultipart(body, contentType) {
  const out = {};
  const m = /boundary=(?:"([^"]+)"|([^;]+))/i.exec(String(contentType || ''));
  if (!m) return out;
  const boundary = (m[1] || m[2] || '').trim();
  if (!boundary) return out;

  const sep = '--' + boundary;
  const parts = body.split(sep);
  for (const part of parts) {
    const idx = part.indexOf('\r\n\r\n');
    if (idx < 0) continue;
    const head = part.slice(0, idx);
    const nameM = /name="([^"]*)"/i.exec(head);
    if (!nameM) continue;
    let val = part.slice(idx + 4);
    // 去掉 part 结尾的 CRLF
    val = val.replace(/\r\n$/, '');
    const name = nameM[1];
    if (Object.prototype.hasOwnProperty.call(out, name)) {
      out[name] = Array.isArray(out[name]) ? out[name].concat([val]) : [out[name], val];
    } else {
      out[name] = val;
    }
  }
  return out;
}

/**
 * 解析请求体 → 普通对象
 * @param {string} body 原始请求体
 * @param {string} contentType 请求头的 content-type
 */
function parseRequestBody(body, contentType) {
  const ct = String(contentType || '').toLowerCase();
  if (!body) return {};
  if (ct.indexOf('multipart/form-data') === 0) return parseMultipart(body, ct);
  if (ct.indexOf('application/json') === 0) {
    try {
      const j = JSON.parse(body);
      return (j && typeof j === 'object' && !Array.isArray(j)) ? j : {};
    } catch (e) {
      return {};
    }
  }
  return querystring.parse(body);
}

module.exports = { parseRequestBody, parseMultipart };

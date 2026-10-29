// Chinawheely P1 — 线索记录（cw_leads）
// 目标：任何一次表单提交都留下一条可查记录；邮件失败也不丢线索。

const crypto = require('crypto');
const { dbConfigured, insert, select, update } = require('./db');

const TABLE = 'cw_leads';
const DEDUPE_WINDOW_SEC = Number(process.env.DEDUPE_WINDOW_SEC || 600); // 幂等时间窗 10 分钟

function generateRef() {
  const ts = Date.now().toString(36).toUpperCase();
  const rand = Math.floor(Math.random() * 10000)
    .toString()
    .padStart(4, '0');
  return `CWC-${ts}-${rand}`;
}

function sha256(str) {
  return crypto.createHash('sha256').update(String(str)).digest('hex');
}

/**
 * 幂等哈希：同一邮箱/电话 + 同一业务内容 → 稳定哈希（不含时间桶，避免跨桶边界漏判）
 * 时间窗判定由 createLead 的查询负责
 */
function buildDedupeKey(record) {
  const parts = [
    (record.email || '').toLowerCase().trim(),
    (record.phone || '').replace(/\D/g, ''),
    record.source || '',
    record.city || '',
    record.subject || '',
    (record.message || '').slice(0, 200),
    JSON.stringify(record.payload && record.payload.__sig ? record.payload.__sig : {})
  ];
  return sha256(parts.join('|')).slice(0, 40);
}

/** 落库；返回 {ok, ref, row, deduped, error} */
async function createLead(record) {
  if (!dbConfigured()) {
    return { ok: false, ref: generateRef(), row: null, deduped: false, error: 'db not configured' };
  }

  const dedupe_key = buildDedupeKey(record);

  // 幂等：同哈希 + 时间窗内（默认 10 分钟）视为同一次提交
  const since = new Date(Date.now() - DEDUPE_WINDOW_SEC * 1000).toISOString();
  const existing = await select(
    TABLE,
    `select=*&dedupe_key=eq.${encodeURIComponent(dedupe_key)}&created_at=gte.${encodeURIComponent(since)}&order=created_at.desc`,
    1
  );
  if (existing.ok && existing.rows.length) {
    return { ok: true, ref: existing.rows[0].ref, row: existing.rows[0], deduped: true, error: '' };
  }

  const row = Object.assign({}, record, { dedupe_key, ref: generateRef() });
  const ins = await insert(TABLE, row);
  if (!ins.ok) {
    return { ok: false, ref: row.ref, row: null, deduped: false, error: ins.error };
  }
  return { ok: true, ref: ins.row ? ins.row.ref : row.ref, row: ins.row, deduped: false, error: '' };
}

/** 更新邮件投递状态 */
async function markMail(ref, status, errorMessage) {
  if (!dbConfigured() || !ref) return { ok: false, error: 'db not configured' };
  const patch = {
    mail_status: status,
    mail_error: errorMessage ? String(errorMessage).slice(0, 500) : null,
    mail_sent_at: status === 'sent' ? new Date().toISOString() : null
  };
  const res = await update(TABLE, `ref=eq.${encodeURIComponent(ref)}`, patch);
  return { ok: res.ok, error: res.error };
}

/** 同 IP 在时间窗内的提交次数（跨实例有效，基于数据库计数） */
async function countRecentByIp(ip, windowSeconds) {
  if (!dbConfigured() || !ip) return { ok: false, count: 0 };
  const since = new Date(Date.now() - windowSeconds * 1000).toISOString();
  const res = await select(
    TABLE,
    `select=id&ip=eq.${encodeURIComponent(ip)}&created_at=gte.${encodeURIComponent(since)}`,
    100
  );
  if (!res.ok) return { ok: false, count: 0 };
  return { ok: true, count: res.rows.length };
}

module.exports = { generateRef, buildDedupeKey, createLead, markMail, countRecentByIp, TABLE };

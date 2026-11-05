// Chinawheely P4 — 订单管理（cw_orders）
// 目标：每次下单生成订单号，状态机可流转，客户可凭订单号自助查单/改期。

const crypto = require('crypto');
const { insert, select, update, dbConfigured } = require('./db');

const TABLE = 'cw_orders';

// 支付状态 / 服务状态 分两层
const PAYMENT_STATUS = ['unpaid', 'payment_submitted', 'paid', 'refunded', 'failed'];
const SERVICE_STATUS = ['pending', 'confirmed', 'in_service', 'completed', 'cancelled', 'no_show'];

function generateOrderRef(date) {
  const d = date || new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const rand = crypto.randomBytes(4).toString('hex').toUpperCase();
  return `CWO-${y}${m}${day}-${rand}`;
}

function sha256(str) {
  return crypto.createHash('sha256').update(String(str)).digest('hex');
}

/** 生成 manage_token（明文给客户，库里只存哈希） */
function generateManageToken() {
  const raw = crypto.randomBytes(24).toString('hex');
  return { raw, hash: sha256(raw) };
}

/** 客户自助链接用的 token 有效期（默认 30 天） */
function manageTokenExpiry(hours) {
  const h = Number(hours || process.env.MANAGE_TOKEN_TTL_HOURS || 720);
  return new Date(Date.now() + h * 3600 * 1000).toISOString();
}

/**
 * 创建订单
 * record: { email, phone, city, product, vehicle, tier, quote, contact, trip, payment }
 */
async function createOrder(record) {
  if (!dbConfigured()) {
    return { ok: false, error: 'DB_NOT_CONFIGURED', ref: null };
  }

  const now = new Date();
  const ref = generateOrderRef(now);
  const token = generateManageToken();

  const row = {
    ref,
    status: 'pending',              // 服务状态
    payment_status: 'unpaid',       // 支付状态
    payment_method: (record.payment && record.payment.method) || null,
    email: (record.email || '').toLowerCase().trim(),
    phone: record.phone || null,
    customer_name: record.customerName || null,
    city: record.city || null,
    product: record.product || null,
    vehicle: record.vehicle || null,
    tier: record.tier || null,
    quote_json: record.quote ? JSON.stringify(record.quote) : null,
    total_cny: record.quote ? record.quote.total : null,
    total_usd: record.quote ? record.quote.usd : null,
    currency: record.quote ? 'CNY' : null,
    pickup_date: record.trip && record.trip.date ? record.trip.date : null,
    pickup_time: record.trip && record.trip.time ? record.trip.time : null,
    pax: record.trip && record.trip.pax ? Number(String(record.trip.pax).replace(/\D/g, '')) || null : null,
    luggage: record.trip && record.trip.luggage ? Number(String(record.trip.luggage).replace(/\D/g, '')) || null : null,
    contact_json: record.contact ? JSON.stringify(record.contact) : null,
    notes: record.notes || null,
    manage_token_hash: token.hash,
    manage_token_expires_at: manageTokenExpiry(),
    admin_note: null,
    created_at: now.toISOString(),
    updated_at: now.toISOString()
  };

  const res = await insert(TABLE, row);
  if (!res.ok) return { ok: false, error: res.error, ref: null };
  return { ok: true, ref, row: res.row, manageToken: token.raw };
}

/** 按订单号查询（公开查单用；可选校验 manage_token）
 *  返回 code 字段供上层映射 HTTP 状态：
 *    OK / NOT_FOUND / TOKEN_MISMATCH / DB_NOT_CONFIGURED / DB_ERROR */
async function getOrderByRef(ref, tokenHash) {
  if (!dbConfigured()) return { ok: false, code: 'DB_NOT_CONFIGURED', error: 'DB_NOT_CONFIGURED', order: null };
  const q = `ref=eq.${encodeURIComponent(ref)}&select=*`;
  const res = await select(TABLE, q, 1);
  if (!res.ok) return { ok: false, code: 'DB_ERROR', error: res.error, order: null };
  const order = res.rows[0] || null;
  if (!order) return { ok: true, code: 'NOT_FOUND', order: null };
  if (tokenHash) {
    if (order.manage_token_hash !== tokenHash) {
      return { ok: false, code: 'TOKEN_MISMATCH', error: 'TOKEN_MISMATCH', order: null };
    }
  }
  return { ok: true, code: 'OK', order };
}

/** 状态流转 */
async function updateOrder(ref, patch) {
  if (!dbConfigured()) return { ok: false, error: 'DB_NOT_CONFIGURED', order: null };
  const allowed = {};
  if (patch.status) {
    if (!SERVICE_STATUS.includes(patch.status)) return { ok: false, error: 'INVALID_STATUS' };
    allowed.status = patch.status;
  }
  if (patch.payment_status) {
    if (!PAYMENT_STATUS.includes(patch.payment_status)) return { ok: false, error: 'INVALID_PAYMENT_STATUS' };
    allowed.payment_status = patch.payment_status;
  }
  if (patch.admin_note !== undefined) allowed.admin_note = patch.admin_note;
  if (patch.manage_token_hash !== undefined) allowed.manage_token_hash = patch.manage_token_hash;
  if (patch.manage_token_expires_at !== undefined) allowed.manage_token_expires_at = patch.manage_token_expires_at;
  if (patch.pickup_date !== undefined) allowed.pickup_date = patch.pickup_date;
  if (patch.pickup_time !== undefined) allowed.pickup_time = patch.pickup_time;
  if (patch.notes !== undefined) allowed.notes = patch.notes;
  if (patch.payment_method !== undefined) allowed.payment_method = patch.payment_method;
  allowed.updated_at = new Date().toISOString();

  const res = await update(TABLE, `ref=eq.${encodeURIComponent(ref)}`, allowed);
  if (!res.ok) return { ok: false, error: res.error, order: null };
  return { ok: true, order: res.rows[0] || null };
}

/** 客户自助改期：48h 规则（按出发时间算） */
function canSelfModify(pickupDateTime) {
  if (!pickupDateTime) return { allowed: false, reason: 'NO_DATE' };
  const t = new Date(pickupDateTime).getTime();
  if (!isFinite(t)) return { allowed: false, reason: 'BAD_DATE' };
  const hoursLeft = (t - Date.now()) / 3600000;
  if (hoursLeft < 48) return { allowed: false, reason: 'WITHIN_48H', hoursLeft };
  return { allowed: true, hoursLeft };
}

module.exports = {
  TABLE,
  PAYMENT_STATUS,
  SERVICE_STATUS,
  generateOrderRef,
  generateManageToken,
  manageTokenExpiry,
  sha256,
  createOrder,
  getOrderByRef,
  updateOrder,
  canSelfModify
};

// Chinawheely P1 — 请求防护（频率限制 + 提交时长校验）
// 频率限制优先用数据库计数（跨实例有效）；数据库不可用时退化为进程内计数。

const { countRecentByIp } = require('./leads');

const memBuckets = new Map(); // ip -> {count, resetAt}

const RATE_LIMIT = Number(process.env.RATE_LIMIT_PER_MINUTE || 5);
const RATE_WINDOW_SEC = 60;
const MIN_FILL_SECONDS = Number(process.env.MIN_FORM_FILL_SECONDS || 3);

/** 进程内计数 */
function memRateLimited(ip) {
  if (!ip) return false;
  const now = Date.now();
  const bucket = memBuckets.get(ip);
  if (!bucket || now > bucket.resetAt) {
    memBuckets.set(ip, { count: 1, resetAt: now + RATE_WINDOW_SEC * 1000 });
    if (memBuckets.size > 5000) memBuckets.clear();
    return false;
  }
  bucket.count += 1;
  return bucket.count > RATE_LIMIT;
}

/**
 * @returns {Promise<{limited:boolean, source:string}>}
 */
async function isRateLimited(ip) {
  const res = await countRecentByIp(ip, RATE_WINDOW_SEC);
  if (res.ok) {
    return { limited: res.count >= RATE_LIMIT, source: 'db' };
  }
  return { limited: memRateLimited(ip), source: 'memory' };
}

/**
 * 表单填写时长校验：页面渲染时间由前端写入 _t 字段
 * 缺字段时不拦截（老前端无此字段）
 */
function filledTooFast(data) {
  const t = Number(data && data._t);
  // 老前端 / 没带时间戳 → 不拦（宁可漏放机器人，也不能误杀真实订单）
  if (!t || Number.isNaN(t) || t <= 0) return false;
  const now = Date.now();
  // 客户端时钟偏差过大（时区错、机器时间不准）→ 不判断
  if (Math.abs(now - t) > 6 * 60 * 60 * 1000) return false;
  const elapsed = now - t;
  if (elapsed < 0) return false;   // 客户端时间超前 → 不拦
  return elapsed < MIN_FILL_SECONDS * 1000;
}

module.exports = { isRateLimited, filledTooFast, RATE_LIMIT, RATE_WINDOW_SEC };

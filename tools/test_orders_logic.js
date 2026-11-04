/**
 * P4 订单逻辑测试：48 小时规则边界、订单号/token 格式、状态枚举
 * 用法: node tools/test_orders_logic.js
 */
const path = require('path');
const orders = require(path.join(__dirname, '..', 'api', '_lib', 'orders'));

let checked = 0;
const fails = [];
function check(cond, msg) {
  checked++;
  if (!cond) fails.push(msg);
}

// ---------- 1. 48h 规则边界 ----------
let r = orders.canSelfModify(new Date(Date.now() + 49 * 3600e3).toISOString());
check(r.allowed === true, `49h 后应可改 (${JSON.stringify(r)})`);

r = orders.canSelfModify(new Date(Date.now() + 48 * 3600e3 + 60e3).toISOString());
check(r.allowed === true, '48h+1min 应可改');

r = orders.canSelfModify(new Date(Date.now() + 48 * 3600e3 - 60e3).toISOString());
check(r.allowed === false && r.reason === 'WITHIN_48H', '48h-1min 应拒绝');

r = orders.canSelfModify(new Date(Date.now() + 47 * 3600e3).toISOString());
check(r.allowed === false, '47h 应拒绝');

r = orders.canSelfModify(new Date(Date.now() - 3600e3).toISOString());
check(r.allowed === false, '过去时间应拒绝');

r = orders.canSelfModify(null);
check(r.allowed === false && r.reason === 'NO_DATE', '无日期应拒绝');

r = orders.canSelfModify('not-a-date');
check(r.allowed === false && r.reason === 'BAD_DATE', '非法日期应拒绝');

// 北京时间字符串
r = orders.canSelfModify('2027-06-01T09:00:00+08:00');
check(typeof r.allowed === 'boolean', '北京时间字符串可解析');

// ---------- 2. 订单号格式 ----------
const ref = orders.generateOrderRef(new Date('2026-11-04T12:00:00+08:00'));
check(/^CWO-20261104-[A-F0-9]{8}$/.test(ref), `订单号格式错: ${ref}`);

// ---------- 3. manage token ----------
const t = orders.generateManageToken();
check(/^[a-f0-9]{48}$/.test(t.raw), `token 明文格式错: ${t.raw}`);
check(/^[a-f0-9]{64}$/.test(t.hash), `token 哈希格式错: ${t.hash}`);
check(orders.sha256(t.raw) === t.hash, '哈希可复算');

// ---------- 4. token 有效期 ----------
const exp = orders.manageTokenExpiry();
check(new Date(exp) > new Date(Date.now() + 29 * 24 * 3600e3), '默认 30 天有效期');
const exp2 = orders.manageTokenExpiry(1);
check(new Date(exp2) > new Date(Date.now() + 55 * 60e3), '自定义 1h 有效期');

// ---------- 5. 状态枚举 ----------
check(orders.SERVICE_STATUS.length === 6, '服务状态应为 6 种');
check(orders.PAYMENT_STATUS.length === 5, '支付状态应为 5 种');
check(orders.SERVICE_STATUS.includes('pending') && orders.SERVICE_STATUS.includes('cancelled'), '服务状态含 pending/cancelled');
check(orders.PAYMENT_STATUS.includes('payment_submitted') && orders.PAYMENT_STATUS.includes('paid'), '支付状态含 payment_submitted/paid');

// ---------- 6. 无 DB 时降级 ----------
orders.createOrder({ email: 'a@b.c' }).then(res => {
  check(res.ok === false && res.error === 'DB_NOT_CONFIGURED', '无 DB 时 createOrder 降级');
  return orders.getOrderByRef('CWO-20260101-AAAAAAAA');
}).then(res => {
  check(res.ok === false && res.error === 'DB_NOT_CONFIGURED', '无 DB 时 getOrderByRef 降级');
  return orders.updateOrder('CWO-20260101-AAAAAAAA', { status: 'confirmed' });
}).then(res => {
  check(res.ok === false, '无 DB 时 updateOrder 降级');

  console.log(`检查项 ${checked}`);
  if (fails.length) {
    console.log(`✗ 失败 ${fails.length}:`);
    fails.forEach(f => console.log('   ', f));
    process.exit(1);
  }
  console.log('✓ 订单逻辑测试全部通过');
});

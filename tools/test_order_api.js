#!/usr/bin/env node
/**
 * api/order.js 回归测试：
 *  1) quote_json 是 jsonb → PostgREST 返回对象，safeParse 必须能直接返回对象
 *  2) 错误状态语义：TOKEN_MISMATCH→403 / 订单不存在→404 / 格式错→400 / DB 故障→503
 * 不打真实数据库：用环境变量注入假数据 + mock fetch。
 */
const assert = require('assert');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

const ORDERS_LIB = path.join(__dirname, '..', 'api', '_lib', 'orders.js');
const DB_LIB = path.join(__dirname, '..', 'api', '_lib', 'db.js');

// ⚠️ 必须在 require api 模块 *之前* 注入 env：
//    api/_lib/db.js 在模块加载时就把 SUPABASE_URL / KEY 捕获到常量里。
process.env.SUPABASE_URL = 'https://fake.supabase.co';
process.env.SUPABASE_SERVICE_ROLE_KEY = 'fake-key';
process.env.ALLOWED_ORIGINS = '*';

let pass = 0, fail = 0;
function t(name, fn) {
  try { fn(); console.log(`  ✅ ${name}`); pass++; }
  catch (e) { console.log(`  ❌ ${name}\n     ${e.message}`); fail++; }
}

// ---------- 1) safeParse：jsonb 对象形态 ----------
console.log('\n【1】safeParse 兼容 jsonb 对象形态');
const orderSrc = fs.readFileSync(
  path.join(__dirname, '..', 'api', 'order.js'), 'utf8');

// 抽出 safeParse 独立测
const safeParseSrc = orderSrc.match(/function safeParse\(\w+\) \{[\s\S]*?\n\}/);
assert(safeParseSrc, '找不到 safeParse');
const safeParse = new Function(`${safeParseSrc[0]}; return safeParse;`)();

t('jsonb 对象 → 原样返回', () => {
  const obj = { total: 328, usd: 46.2, lines: [{ name: 'x', pkg: 328 }] };
  assert.deepStrictEqual(safeParse(obj), obj);
});
t('JSON 字符串 → 解析成对象', () => {
  assert.deepStrictEqual(safeParse('{"total":328}'), { total: 328 });
});
t('null / undefined / 空串 → null', () => {
  assert.strictEqual(safeParse(null), null);
  assert.strictEqual(safeParse(undefined), null);
  assert.strictEqual(safeParse(''), null);
});
t('非法 JSON 字符串 → null（不抛异常）', () => {
  assert.strictEqual(safeParse('{not json'), null);
});
t('数字/布尔 → null', () => {
  assert.strictEqual(safeParse(123), null);
  assert.strictEqual(safeParse(true), null);
});

// ---------- 2) 错误状态语义 ----------
console.log('\n【2】HTTP 状态语义');

const orderMod = require(ORDERS_LIB);
// 替换 db 模块，让 select 返回我们想要的
const dbPath = require.resolve(DB_LIB);
const realDb = require(DB_LIB);

function makeReq(method, url, body) {
  const req = {
    method, url, headers: { origin: 'https://www.chinawheely.com' },
    on(ev, cb) {
      if (ev === 'data') cb(Buffer.from(body || ''));
      if (ev === 'end') cb();
      if (ev === 'error') cb(new Error('x'));
      return req;
    }
  };
  return req;
}
function makeRes() {
  const res = {
    statusCode: 200, headers: {}, body: '',
    setHeader(k, v) { this.headers[k] = v; },
    end(b) { this.body = b || ''; this.finished = true; return this; }
  };
  return res;
}
async function callApi(method, url, body) {
  const req = makeReq(method, url, body);
  const res = makeRes();
  await require(path.join(__dirname, '..', 'api', 'order.js'))(req, res);
  let json = null;
  try { json = JSON.parse(res.body); } catch (e) { /* noop */ }
  return { status: res.statusCode, body: json, raw: res.body };
}

(async () => {
  const realFetch = global.fetch;
  let mode = 'ok';

  // 构造一行假订单
  const rawToken = 'a'.repeat(48);
  const tokenHash = crypto.createHash('sha256').update(rawToken).digest('hex');
  const goodRef = 'CWO-20261105-DEADBEEF';
  const row = {
    ref: goodRef, status: 'pending', payment_status: 'unpaid',
    city: 'Beijing', product: 'airport', vehicle: 'sedan_economy', tier: null,
    total_cny: 328, total_usd: 46.2, currency: 'CNY',
    pickup_date: '2026-12-20', pickup_time: '10:00', pax: 2, luggage: 2,
    notes: null, created_at: '2026-11-05T00:00:00Z', updated_at: '2026-11-05T00:00:00Z',
    // 关键：jsonb 列返回的是「已解析对象」，不是字符串
    quote_json: { total: 328, usd: 46.2, lines: [{ name: '4座 经济型专车', pkg: 328 }] },
    manage_token_hash: tokenHash,
    manage_token_expires_at: '2027-01-01T00:00:00Z'
  };

  let mode2 = mode;
  global.fetch = async (url) => {
    if (mode2 === 'db_error') return { ok: false, status: 500, text: async () => '{"message":"boom"}' };
    if (mode2 === 'not_found') return { ok: true, status: 200, text: async () => '[]' };
    return { ok: true, status: 200, text: async () => JSON.stringify([row]) };
  };

  console.log('\n  --- 正常路径 ---');
  const ok = await callApi('GET', `/api/order?ref=${goodRef}&token=${rawToken}`);
  t('GET 正确 ref+token → 200', () => assert.strictEqual(ok.status, 200));
  t('quote_json 对象被正确返回（不是 null）', () => {
    assert.ok(ok.body && ok.body.order, '无 order');
    assert.ok(ok.body.order.quote, 'quote 为 null —— jsonb 解析 bug 未修');
    assert.strictEqual(ok.body.order.quote.total, 328);
    assert.strictEqual(ok.body.order.quote.lines[0].pkg, 328);
  });
  t('self_modify 结构存在', () => {
    assert.ok(ok.body.self_modify && typeof ok.body.self_modify.allowed === 'boolean');
  });

  console.log('\n  --- 错误路径 ---');
  const wrongTok = await callApi('GET', `/api/order?ref=${goodRef}&token=${'b'.repeat(48)}`);
  t('token 不匹配 → 403（不是 500）', () => {
    assert.strictEqual(wrongTok.status, 403);
    assert.strictEqual(wrongTok.body.code, 'TOKEN_MISMATCH');
  });
  t('403 响应带 hint 与客服联系方式', () => {
    assert.ok(wrongTok.body.hint, '缺 hint');
    assert.ok(wrongTok.body.support, '缺 support');
    assert.ok(!('detail' in wrongTok.body), '403 不应回传内部 detail');
  });

  mode2 = 'not_found';
  const nf = await callApi('GET', `/api/order?ref=${'CWO-20261105-00000000'}&token=${rawToken}`);
  t('订单不存在 → 404', () => {
    assert.strictEqual(nf.status, 404);
    assert.strictEqual(nf.body.code, 'NOT_FOUND');
  });

  mode2 = 'ok';
  const badRef = await callApi('GET', `/api/order?ref=NOPE&token=${rawToken}`);
  t('ref 格式错 → 400', () => assert.strictEqual(badRef.status, 400));
  const badTok = await callApi('GET', `/api/order?ref=${goodRef}&token=xyz`);
  t('token 格式错 → 400', () => assert.strictEqual(badTok.status, 400));

  mode2 = 'db_error';
  const dbErr = await callApi('GET', `/api/order?ref=${goodRef}&token=${rawToken}`);
  t('数据库故障 → 503（可重试，不是 500）', () => {
    assert.strictEqual(dbErr.status, 503);
    assert.strictEqual(dbErr.body.code, 'DB_ERROR');
  });
  t('5xx 响应回传 detail 便于排查', () => {
    assert.ok(dbErr.body.detail, '缺 detail');
  });

  // PATCH 也走同一条 authOrder
  mode2 = 'ok';
  const patchWrong = await callApi('PATCH', '/api/order',
    JSON.stringify({ ref: goodRef, token: 'b'.repeat(48), pickup_date: '2026-12-25' }));
  t('PATCH token 不匹配 → 403', () => assert.strictEqual(patchWrong.status, 403));

  global.fetch = realFetch;

  console.log(`\n${'='.repeat(50)}`);
  console.log(fail === 0 ? `✅ 全部通过（${pass} 项）` : `❌ 失败 ${fail} 项 / 通过 ${pass} 项`);
  process.exit(fail === 0 ? 0 : 1);
})();

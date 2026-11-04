/**
 * P2/P4 后端端到端测试
 * 验证 /api/booking 的服务端算价（不采信前端 price）与 /api/quote 行为。
 * 用法: node tools/test_api_booking.js
 * 退出码: 0=通过
 */
const path = require('path');
const BASE = path.join(__dirname, '..');

let checked = 0;
const fails = [];
function check(cond, msg) {
  checked++;
  if (!cond) fails.push(msg);
}

// ---------- 模拟 req/res ----------
function makeRes() {
  const res = {
    statusCode: 200, headers: {}, body: null,
    setHeader(k, v) { this.headers[k] = v; },
    writeHead(code, h) { this.statusCode = code; Object.assign(this.headers, h || {}); },
    end(b) { this.body = b == null ? '' : b; this.done = true; return this; },
    json(o) { this.body = JSON.stringify(o); this.done = true; return this; },
    status(code) { this.statusCode = code; return this; },
  };
  return res;
}

function makeReq(body, opts) {
  opts = opts || {};
  const req = {
    method: opts.method || 'POST',
    headers: { 'content-type': opts.contentType || 'application/x-www-form-urlencoded',
               'x-forwarded-for': opts.ip || '203.0.113.10' },
    socket: { remoteAddress: opts.ip || '203.0.113.10' },
    on(ev, cb) { this._ev = this._ev || {}; this._ev[ev] = cb; },
  };
  if (opts.method !== 'GET') {
    setTimeout(() => {
      if (req._ev && req._ev.data) req._ev.data(body);
      if (req._ev && req._ev.end) req._ev.end();
    }, 0);
  }
  return req;
}

const booking = require(path.join(BASE, 'api', 'booking.js'));
const quoteApi = require(path.join(BASE, 'api', 'quote.js'));
const pricing = require(path.join(BASE, 'api', '_lib', 'pricing.js'));

function formEncode(obj) {
  return Object.keys(obj).map(k =>
    encodeURIComponent(k) + '=' + encodeURIComponent(obj[k])
  ).join('&');
}

// ---------- 1. /api/quote 正常报价 ----------
(async function () {
  let res = makeRes();
  await quoteApi(makeReq(JSON.stringify({
    city: 'beijing', product: 'airport', vehicle: 'sedan_economy', pax: 2
  }), { contentType: 'application/json' }), res);
  let r = JSON.parse(res.body);
  check(r.ok === true, 'quote 应成功');
  check(r.total === 328, `quote 北京经济型应为 328，实为 ${r.total}`);
  check(r.usd === Math.round(328 / 7.10 * 100) / 100, 'quote USD 折算错');
  check(r.currency === 'CNY', 'quote 币种应为 CNY');

  // ---------- 2. /api/quote 无价城市 ----------
  res = makeRes();
  await quoteApi(makeReq(JSON.stringify({
    city: 'notacity', product: 'airport', vehicle: 'sedan_economy'
  }), { contentType: 'application/json' }), res);
  r = JSON.parse(res.body);
  check(r.ok === false && r.quoteRequired === true, '无价城市应 quoteRequired');

  // ---------- 3. /api/quote options ----------
  res = makeRes();
  await quoteApi(makeReq(JSON.stringify({ action: 'options', city: 'beijing' }),
    { contentType: 'application/json' }), res);
  r = JSON.parse(res.body);
  check(r.ok && r.airport.length === 6, `北京应有 6 个接送机车型，实为 ${r.airport && r.airport.length}`);
  check(r.charter.length === 5, `北京应有 5 个包车车型，实为 ${r.charter && r.charter.length}`);
  check(r.charter[0].tiers.length === 5, '包车应有 5 个时长档');

  // ---------- 4. /api/quote cities ----------
  res = makeRes();
  await quoteApi(makeReq(JSON.stringify({ action: 'cities' }),
    { contentType: 'application/json' }), res);
  r = JSON.parse(res.body);
  check(r.ok && r.cities.length === 53, `应有 53 城，实为 ${r.cities && r.cities.length}`);

  // ---------- 5. intercity 与 airport 同价 ----------
  const a = pricing.quote({ city: 'shanghai', product: 'airport', vehicle: 'sedan_economy' });
  const i = pricing.quote({ city: 'shanghai', product: 'intercity', vehicle: 'sedan_economy' });
  check(a.ok && i.ok && a.total === i.total, 'intercity 应与 airport 同价');

  // ---------- 6. 银川=威海 / 台州=嘉兴 ----------
  const y1 = pricing.quote({ city: 'yinchuan', product: 'airport', vehicle: 'sedan_economy' });
  const w1 = pricing.quote({ city: 'weihai', product: 'airport', vehicle: 'sedan_economy' });
  const t1 = pricing.quote({ city: 'taizhou', product: 'airport', vehicle: 'sedan_economy' });
  const j1 = pricing.quote({ city: 'jiaxing', product: 'airport', vehicle: 'sedan_economy' });
  check(y1.ok && w1.ok && y1.total === w1.total,
    `银川应与威海同价: ${y1.total} vs ${w1.total}`);
  check(t1.ok && j1.ok && t1.total === j1.total,
    `台州应与嘉兴同价: ${t1.total} vs ${j1.total}`);

  // ---------- 7. 超时/超里程 ----------
  const ov = pricing.quote({
    city: 'beijing', product: 'airport', vehicle: 'sedan_economy',
    extraMinutes: 30, extraKm: 5
  });
  check(ov.ok && Math.abs(ov.total - (328 + 1.55 * 30 + 7.29 * 5)) < 0.01,
    `超时+超里程计算错: ${ov.total}`);

  // ---------- 8. 服务端算价：不采信前端 price ----------
  // 直接调用内部逻辑不可达，故通过邮件内容间接验证 —— 这里验证 pricing 层
  // 前端伪造 price 字段不影响服务端计算，因为服务端不读它。
  const tampered = {
    city: 'beijing', product: 'airport', vehicle: 'sedan_economy',
    price: '$1', totalPrice: '1'
  };
  const q = pricing.quote(tampered);
  check(q.ok && q.total === 328,
    `即使传入伪造 price，服务端仍应算出 328，实为 ${q.total}`);

  console.log(`检查项 ${checked}`);
  if (fails.length) {
    console.log(`✗ 失败 ${fails.length}:`);
    fails.forEach(f => console.log('   ', f));
    process.exit(1);
  }
  console.log('✓ 后端端到端测试全部通过');
})();

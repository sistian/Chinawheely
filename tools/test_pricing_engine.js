/**
 * 定价引擎自测 (Node)
 * 校验 api/_lib/pricing.js 的算价结果与 pricing.json 一致，且关键业务规则成立。
 * 用法: node tools/test_pricing_engine.js
 * 退出码: 0=通过, 1=失败
 */
const path = require('path');
const fs = require('fs');

const BASE = path.join(__dirname, '..');
const pricing = require(path.join(BASE, 'api', '_lib', 'pricing.js'));

let checked = 0;
const fails = [];

function check(cond, msg) {
  checked++;
  if (!cond) fails.push(msg);
}

const data = pricing.loadPricing();

// ---------- 1. 基础报价 = 套餐价 ----------
for (const slug of Object.keys(data.cities)) {
  const c = data.cities[slug];
  for (const vkey of Object.keys(c.airport)) {
    const r = pricing.quote({ city: slug, product: 'airport', vehicle: vkey, pax: 1 });
    check(r.ok, `${slug}/${vkey} 接送机报价失败: ${r.error}`);
    if (r.ok) {
      check(r.total === c.airport[vkey].pkg,
        `${slug}/${vkey} 接送机总价应=${c.airport[vkey].pkg} 实=${r.total}`);
      check(r.currency === 'CNY', `${slug}/${vkey} 币种应为 CNY`);
      check(r.usd === Math.round(r.total / 7.10 * 100) / 100,
        `${slug}/${vkey} USD 折算错误: ${r.usd}`);
      check(r.lines.length === 1, `${slug}/${vkey} 无加收项时应只有 1 行明细`);
    }
  }
  for (const vkey of Object.keys(c.charter)) {
    for (const tk of Object.keys(c.charter[vkey].tiers)) {
      const r = pricing.quote({ city: slug, product: 'charter', vehicle: vkey, tier: tk, pax: 1 });
      check(r.ok, `${slug}/${vkey}/${tk} 包车报价失败: ${r.error}`);
      if (r.ok) {
        check(r.total === c.charter[vkey].tiers[tk].pkg,
          `${slug}/${vkey}/${tk} 包车总价应=${c.charter[vkey].tiers[tk].pkg} 实=${r.total}`);
      }
    }
  }
}

// ---------- 2. 超时 / 超里程 加算 ----------
const bj = 'beijing';
const econ = data.cities[bj].airport.sedan_economy;
let r = pricing.quote({ city: bj, product: 'airport', vehicle: 'sedan_economy', extraMinutes: 30, pax: 1 });
check(r.ok && Math.abs(r.total - (econ.pkg + econ.perMin * 30)) < 0.01,
  `超时 30 分钟计算错误: ${r.total} vs ${econ.pkg + econ.perMin * 30}`);
check(r.lines.length === 2, '超时后应有 2 行明细');

r = pricing.quote({ city: bj, product: 'airport', vehicle: 'sedan_economy', extraKm: 5, pax: 1 });
check(r.ok && Math.abs(r.total - (econ.pkg + econ.perKm * 5)) < 0.01,
  `超里程 5 公里计算错误: ${r.total}`);

r = pricing.quote({ city: bj, product: 'airport', vehicle: 'sedan_economy', extraMinutes: 45, extraKm: 12, pax: 1 });
const expect = econ.pkg + econ.perMin * 45 + econ.perKm * 12;
check(r.ok && Math.abs(r.total - expect) < 0.01, `组合加收计算错误: ${r.total} vs ${expect}`);

// ---------- 3. Intercity 与 接送机 同价 ----------
for (const slug of ['beijing', 'shanghai', 'chengdu']) {
  const a = pricing.quote({ city: slug, product: 'airport', vehicle: 'sedan_economy', pax: 1 });
  const i = pricing.quote({ city: slug, product: 'intercity', vehicle: 'sedan_economy', pax: 1 });
  check(a.ok && i.ok && a.total === i.total,
    `${slug} intercity 应与 airport 同价: ${a.total} vs ${i.total}`);
}

// ---------- 4. 银川 = 威海、台州 = 嘉兴 整城同价 ----------
const pairs = [['yinchuan', 'weihai'], ['taizhou', 'jiaxing']];
for (const [t, s] of pairs) {
  for (const vkey of Object.keys(data.cities[t].airport)) {
    const a = pricing.quote({ city: t, product: 'airport', vehicle: vkey, pax: 1 });
    const b = pricing.quote({ city: s, product: 'airport', vehicle: vkey, pax: 1 });
    check(a.ok && b.ok && a.total === b.total,
      `${t}/${vkey} 应与 ${s} 同价: ${a.total} vs ${b.total}`);
  }
  for (const vkey of Object.keys(data.cities[t].charter)) {
    for (const tk of Object.keys(data.cities[t].charter[vkey].tiers)) {
      const a = pricing.quote({ city: t, product: 'charter', vehicle: vkey, tier: tk, pax: 1 });
      const b = pricing.quote({ city: s, product: 'charter', vehicle: vkey, tier: tk, pax: 1 });
      check(a.ok && b.ok && a.total === b.total,
        `${t}/包车/${vkey}/${tk} 应与 ${s} 同价`);
    }
  }
}

// ---------- 5. 汇率固定 7.10 ----------
check(pricing.rate() === 7.10, `汇率应为 7.10，实为 ${pricing.rate()}`);
const q1 = pricing.quote({ city: 'beijing', product: 'airport', vehicle: 'sedan_economy', pax: 1 });
check(Math.abs(q1.usd - q1.total / 7.10) < 0.01, 'USD 应按固定 7.10 折算');

// ---------- 6. 无价场景 ----------
let bad = pricing.quote({ city: 'notacity', product: 'airport', vehicle: 'sedan_economy', pax: 1 });
check(!bad.ok && bad.quoteRequired === true, '未知城市应返回 quoteRequired');
bad = pricing.quote({ city: 'beijing', product: 'airport', vehicle: 'nonexistent', pax: 1 });
check(!bad.ok && bad.quoteRequired === true, '未知车型应返回 quoteRequired');
bad = pricing.quote({ city: 'beijing', product: 'charter', vehicle: 'sedan_4', tier: 'nope', pax: 1 });
check(!bad.ok && bad.quoteRequired === true, '未知档位应返回 quoteRequired');

// ---------- 7. 载客超限告警 ----------
const over = pricing.quote({ city: 'beijing', product: 'airport', vehicle: 'sedan_economy', pax: 9 });
check(over.ok && over.warnings.some(w => w.includes('限乘')),
  '4 座车型载 9 人应产生告警');
const okFit = pricing.quote({ city: 'beijing', product: 'airport', vehicle: 'sedan_economy', pax: 4 });
check(okFit.ok && !okFit.warnings.some(w => w.includes('限乘')), '4 人乘坐 4 座车不应告警');

// ---------- 8. 城市清单 ----------
const cities = pricing.listPricedCities();
check(cities.length === 53, `有价城市应为 53，实为 ${cities.length}`);
check(cities.every(c => c.fromCny > 0), '每个城市都应有起价');
const beijingEntry = cities.find(c => c.slug === 'beijing');
check(beijingEntry && beijingEntry.fromCny === 328,
  `北京起价应为 328（4座经济型），实为 ${beijingEntry && beijingEntry.fromCny}`);

// ---------- 9. 产品别名兼容 ----------
const aliasCity = pricing.quote({ city: 'Beijing', product: 'city', vehicle: 'sedan_4', tier: '4h_50km', pax: 1 });
check(aliasCity.ok, '别名 product=city 应映射到 charter，且城市名大小写不敏感');
const aliasCity2 = pricing.quote({ city: 'beijing', product: 'city', vehicle: 'sedan_4', tier: '4h_50km', pax: 1 });
check(aliasCity2.ok && aliasCity2.total === aliasCity.total, '别名映射结果应一致');

// ---------- 10. 小数精度 ----------
const frac = pricing.quote({ city: 'beijing', product: 'airport', vehicle: 'sedan_economy', extraKm: 3, pax: 1 });
check(Math.abs(frac.total - (328 + 7.29 * 3)) < 0.005, '小数加收精度错误');

console.log(`检查项 ${checked}`);
if (fails.length) {
  console.log(`✗ 失败 ${fails.length}:`);
  fails.slice(0, 25).forEach(f => console.log('   ', f));
  process.exit(1);
}
console.log('✓ 定价引擎全部通过');

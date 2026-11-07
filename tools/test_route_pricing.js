const path = require('path');
const core = require(path.join(__dirname, '..', 'js', 'pricing-core.js'));
const data = require(path.join(__dirname, '..', 'pricing', 'pricing.json'));

function show(title, opts) {
  const q = core.quote(data, opts);
  if (!q.ok) { console.log(title, '=> 失败', q.error); return; }
  console.log('\n■ ' + title);
  console.log('  套餐: ' + q.lines[0].label + '  ¥' + q.lines[0].amount);
  q.lines.slice(1).forEach(l => console.log('  附加: ' + l.label + '  ¥' + l.amount));
  console.log('  含: ' + q.includedKm + ' km + ' + q.includedMinutes + ' min | 客人填: ' +
    (q.routeKm === null ? '-' : q.routeKm) + ' km / ' + (q.routeMinutes === null ? '-' : q.routeMinutes) + ' min');
  console.log('  实超: ' + q.extraKmRaw + ' km / ' + q.extraMinutesRaw + ' min  → 计费: ' + q.billedKm + ' km / ' + q.billedMinutes + ' min');
  console.log('  合计: ¥' + q.total + '  ≈$' + q.usd);
}

// 1) 机场接送：北京，4座经济型，35km 含，60min 含
show('北京 接送机 · 客人填 48km/65min（超 13km/5min）', {
  city: 'beijing', product: 'airport', vehicle: 'sedan_economy',
  routeKm: 48, routeMinutes: 65
});
// 2) 路线在套餐内 → 不产生任何附加费
show('北京 接送机 · 客人填 30km/40min（完全在套餐内）', {
  city: 'beijing', product: 'airport', vehicle: 'sedan_economy',
  routeKm: 30, routeMinutes: 40
});
// 3) 超时 25 分钟 → 按 30 分钟块计（报价单口径）
show('北京 接送机 · 客人填 35km/85min（超 0km/25min → 30min块）', {
  city: 'beijing', product: 'airport', vehicle: 'sedan_economy',
  routeKm: 35, routeMinutes: 85
});
// 4) 超里程 12km → 按 15km 块计
show('北京 接送机 · 客人填 47km/50min（超 12km → 15km块）', {
  city: 'beijing', product: 'airport', vehicle: 'sedan_economy',
  routeKm: 47, routeMinutes: 50
});
// 5) 包车 4H/50KM：含 4 小时 240 分钟、50km
show('北京 包车 4H-50KM · 客人填 95km/330min（超 45km/90min）', {
  city: 'beijing', product: 'charter', vehicle: 'sedan_4', tier: '4h_50km',
  routeKm: 95, routeMinutes: 330
});
// 6) 包车：客人实际只开了 2 小时 → 套餐内，无附加
show('北京 包车 4H-50KM · 客人填 45km/120min（套餐内）', {
  city: 'beijing', product: 'charter', vehicle: 'sedan_4', tier: '4h_50km',
  routeKm: 45, routeMinutes: 120
});
// 7) 城际（同接送机价）
show('北京 城际 · 客人填 1200km/720min（长途 → 全额附加）', {
  city: 'beijing', product: 'intercity', vehicle: 'sedan_economy',
  routeKm: 1200, routeMinutes: 720
});
// 8) 旧字段兼容（extraKm/extraMinutes 仍可用）
show('北京 接送机 · 旧字段 extraKm=13 / extraMinutes=5', {
  city: 'beijing', product: 'airport', vehicle: 'sedan_economy',
  extraKm: 13, extraMinutes: 5
});
// 9) 空值（不填）→ 无附加费
show('北京 接送机 · 什么都没填', {
  city: 'beijing', product: 'airport', vehicle: 'sedan_economy'
});
// 10) 0 值（填了 0km）→ 按套餐内处理
show('北京 接送机 · 填 0km/0min', {
  city: 'beijing', product: 'airport', vehicle: 'sedan_economy',
  routeKm: 0, routeMinutes: 0
});
// 11) 上海 6座商务车
show('上海 接送机 6座 · 客人填 60km/75min', {
  city: 'shanghai', product: 'airport', vehicle: 'mpv_6',
  routeKm: 60, routeMinutes: 75
});

/**
 * 服务端权威算价测试（直接调用 api/booking.js 的 computePrice）
 * 用法：node tools/test_booking_pricing.js
 */
const booking = require('../api/booking.js');
const computePrice = booking.computePrice;

const base = {
  firstName: 'Test', lastName: 'User', email: 'probe@example.com', phone: '+8615000000000',
  city: 'beijing', product: 'airport', vehicle: 'sedan_economy',
  airport: 'Beijing Capital (PEK)', transferDirection: 'airport-to-hotel',
  hotelAddress: 'Test Hotel', date: '2026-12-01', time: '10:00',
  passengers: '2', luggage: '1',
};

function t(name, extra) {
  const data = Object.assign({}, base, extra);
  const r = computePrice(data);
  if (!r.ok) { console.log('\n■ ' + name + '\n  失败: ' + r.reason + ' ' + (r.quote && r.quote.message || '')); return; }
  const q = r.quote;
  console.log('\n■ ' + name);
  q.lines.forEach(l => console.log('   ' + l.label + '  →  ¥' + l.amount));
  console.log('   含: ' + q.includedKm + ' km + ' + q.includedMinutes + ' min | 客人填: ' +
    (q.routeKm === null ? '-' : q.routeKm) + ' km / ' + (q.routeMinutes === null ? '-' : q.routeMinutes) + ' min' +
    ' | 实超 ' + q.extraKmRaw + ' km / ' + q.extraMinutesRaw + ' min → 计费 ' + q.billedKm + ' km / ' + q.billedMinutes + ' min');
  console.log('   合计 ¥' + q.total + ' ≈$' + q.usd);
  if (q.warnings && q.warnings.length) q.warnings.forEach(w => console.log('   ⚠ ' + w));
}

t('① 机场接送 · 填 48km/65min（超 13km/5min → 15km/30min）', { routeKm: '48', routeMinutes: '65' });
t('② 机场接送 · 填 30km/40min（套餐内 → 无附加）', { routeKm: '30', routeMinutes: '40' });
t('③ 机场接送 · 不填路线（沿用标准路线）', {});
t('④ 机场接送 · 选了距离档 80+ 但没填精确里程（兼容旧逻辑）', { distanceRange: '80+' });
t('⑤ 机场接送 · 距离档 35-50（超 7.5km → 10km 块）', { distanceRange: '35-50' });
t('⑥ 包车 4H-50KM · 填 95km/330min', {
  product: 'charter', vehicle: 'sedan_4', tier: '4h_50km',
  charterRoute: 'Terracotta Warriors', routeKm: '95', routeMinutes: '330',
});
t('⑦ 城际 · 填 1200km/720min（不叠加机场超里程）', {
  product: 'intercity', fromCity: 'Beijing', toCity: 'Shanghai',
  routeKm: '1200', routeMinutes: '720',
});
t('⑧ 上海 6座商务车 · 填 60km/75min', {
  city: 'shanghai', vehicle: 'mpv_6', routeKm: '60', routeMinutes: '75',
});
t('⑨ 恶意输入：routeKm=abc / routeMinutes=-50', { routeKm: 'abc', routeMinutes: '-50' });
t('⑩ 恶意输入：routeKm=99999', { routeKm: '99999', routeMinutes: '99999' });

/**
 * 本地端到端测试：模拟 POST /api/booking，验证服务端权威算价
 * 用法：node tools/test_booking_api.js
 */
const querystring = require('querystring');

process.env.RECIPIENT_EMAIL = 'test@example.com';
process.env.ALLOWED_ORIGINS = '*';

const booking = require('../api/booking.js');

function makeReq(body) {
  return {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded', 'x-forwarded-for': '1.2.3.4' },
    on: () => {},
    setTimeout: () => {},
    socket: { remoteAddress: '1.2.3.4' },
    _body: body,
  };
}

function makeRes() {
  const res = {
    statusCode: 200,
    headers: {},
    setHeader(k, v) { this.headers[k] = v; },
    getHeader(k) { return this.headers[k]; },
    end(body) { this._body = body; this._done = true; },
    status(c) { this.statusCode = c; return this; },
    json(o) { this._body = JSON.stringify(o); this._done = true; },
    _done: false, _body: '',
  };
  return res;
}

async function run(name, fields) {
  const req = makeReq(querystring.stringify(fields));
  const res = makeRes();
  // 读取 body（api/_lib/body.js 需要流，这里直接给字符串）
  req.on = function (ev, cb) { if (ev === 'data') cb(Buffer.from(req._body)); if (ev === 'end') cb(); };
  req.setTimeout = function () {};
  await booking(req, res);
  let out = {};
  try { out = JSON.parse(res._body); } catch (e) { out = { raw: String(res._body).slice(0, 200) }; }
  console.log('\n■ ' + name);
  console.log('  status=' + res.statusCode + '  ' + JSON.stringify(out).slice(0, 400));
  return out;
}

(async function () {
  const base = {
    firstName: 'Test', lastName: 'User', email: 'probe@example.com', phone: '+8615000000000',
    city: 'beijing', product: 'airport', vehicle: 'sedan_economy',
    airport: 'Beijing Capital (PEK)', transferDirection: 'airport-to-hotel',
    hotelAddress: 'Test Hotel', date: '2026-12-01', time: '10:00',
    passengers: '2', luggage: '1', serviceType: 'airport', serviceTypeLabel: 'Airport Transfer',
  };

  await run('① 机场接送 · 填 48km/65min（超 13km/5min → 15km/30min）',
    Object.assign({}, base, { routeKm: '48', routeMinutes: '65' }));

  await run('② 机场接送 · 填 30km/40min（套餐内 → 无附加）',
    Object.assign({}, base, { routeKm: '30', routeMinutes: '40' }));

  await run('③ 机场接送 · 不填路线（沿用标准路线）',
    Object.assign({}, base, { distanceRange: '0-35' }));

  await run('④ 机场接送 · 选了距离档 80+ 但没填精确里程（兼容旧逻辑）',
    Object.assign({}, base, { distanceRange: '80+' }));

  await run('⑤ 包车 4H-50KM · 填 95km/330min',
    Object.assign({}, base, {
      product: 'charter', vehicle: 'sedan_4', tier: '4h_50km',
      charterRoute: 'Terracotta Warriors', routeKm: '95', routeMinutes: '330',
    }));

  await run('⑥ 城际 · 填 1200km/720min（不应叠加机场超里程）',
    Object.assign({}, base, {
      product: 'intercity', fromCity: 'Beijing', toCity: 'Shanghai',
      routeKm: '1200', routeMinutes: '720',
    }));

  await run('⑦ 加购儿童座椅 + WiFi',
    Object.assign({}, base, {
      routeKm: '40', routeMinutes: '50',
      extras: ['childseat', 'wifi', 'meetgreet'],
      notes: 'Child seat needed',
    }));
})();

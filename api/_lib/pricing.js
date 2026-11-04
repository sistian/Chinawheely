/**
 * Chinawheely 定价引擎（Node 侧包装）
 *
 * 权威算价入口 —— 服务端下单用。
 * 核心算法在 js/pricing-core.js（前后端共用），本文件只负责：
 *   1) 读盘 pricing/pricing.json
 *   2) 暴露与前端一致的 API
 *
 * 币种：CNY 为主，USD 参考（固定汇率 1 USD = 7.10 CNY）
 * 口径：Intercity 与接送机同价；银川=威海、台州=嘉兴整城同价
 */

const fs = require('fs');
const path = require('path');

const core = require(path.join(__dirname, '..', '..', 'js', 'pricing-core.js'));

let PRICING = null;

function loadPricing() {
  if (PRICING) return PRICING;
  const candidates = [
    path.join(__dirname, '..', '..', 'pricing', 'pricing.json'),
    path.join(__dirname, '..', '..', '..', 'pricing', 'pricing.json'),
    path.join(process.cwd(), 'pricing', 'pricing.json'),
  ];
  for (const p of candidates) {
    try {
      if (fs.existsSync(p)) {
        PRICING = JSON.parse(fs.readFileSync(p, 'utf8'));
        return PRICING;
      }
    } catch (e) { /* try next */ }
  }
  throw new Error('pricing.json not found');
}

/** 环境变量可覆盖汇率（默认 7.10） */
function rate() {
  const v = parseFloat(process.env.USD_CNY_RATE);
  return v > 0 ? v : core.rate(loadPricing());
}

function quote(opts) {
  const data = loadPricing();
  const r = core.quote(data, opts);
  if (r.ok) {
    r.usdRate = rate();
    r.usd = core.round2(r.total / rate());
  }
  return r;
}

function lowestPrice(city, product) {
  const r = core.lowestPrice(loadPricing(), city, product);
  if (!r) return null;
  return { cny: r.cny, usd: core.round2(r.cny / rate()) };
}

function listPricedCities() {
  return core.listPricedCities(loadPricing());
}

function cityOptions(city) {
  return core.cityOptions(loadPricing(), city);
}

function getCity(city) {
  return core.getCity(loadPricing(), city);
}

module.exports = {
  quote,
  lowestPrice,
  listPricedCities,
  cityOptions,
  getCity,
  cityKey: core.cityKey,
  toUsd: (cny) => core.round2(cny / rate()),
  rate,
  PRODUCTS: core.PRODUCTS,
  normalizeProduct: core.normalizeProduct,
  loadPricing,
  core,
};

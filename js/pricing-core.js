/**
 * Chinawheely 定价核心（前后端共用）
 *
 * 纯函数，不依赖 fs / DOM —— 浏览器 <script> 与 Node require() 均可加载。
 * 数据由 pricing/pricing.json 提供（Node 侧由 api/_lib/pricing.js 读盘注入）。
 *
 * 口径（2026-11-04 用户确认）:
 *   - 币种 CNY 为主，USD 参考，固定汇率 1 USD = 7.10 CNY
 *   - Intercity 城际 与 接送机 同价
 *   - 银川 = 威海同价；台州 = 嘉兴同价（生成阶段整城替换）
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.CWPricing = factory();
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var DEFAULT_USD_CNY_RATE = 7.10;

  // 车型英文名（预订页面向外国客人，不出现中文）
  var VEHICLE_EN = {
    sedan_economy: '4-seat Economy Sedan',
    sedan_comfort: '4-seat Premium Sedan',
    sedan_4: '4-seat Sedan',
    mpv_6: '6-seat MPV',
    van_8_11: '8-11 seat Minivan',
    van_12_18: '12-18 seat Minibus',
    coach_19_55: '19-55 seat Coach',
  };

  function vehicleEn(key) {
    return VEHICLE_EN[key] || key;
  }

  // 时长档英文名（charter）
  function tierEn(tier) {
    var h = tier.hours ? tier.hours + ' hours' : '';
    var km = tier.includedKm ? tier.includedKm + ' km included' : '';
    if (h && km) return h + ' / ' + km;
    return h || km || 'Package';
  }

  var PRODUCTS = {
    airport: {
      key: 'airport',
      label: 'Airport Transfer',
      table: 'airport',
      includedKm: 35,
    },
    intercity: {
      key: 'intercity',
      label: 'Intercity Transfer',
      table: 'airport',   // 城际与接送机同价
      includedKm: 35,
      // 城际按出发城市一口价，不叠加机场接送的超时/超里程（否则长途会算出荒谬价格）
      noOverage: true,
    },
    charter: {
      key: 'charter',
      label: 'Hourly Charter',
      table: 'charter',
      includedKm: null,
    },
  };

  var PRODUCT_ALIASES = {
    airport: 'airport',
    'airport-transfer': 'airport',
    'point-to-point': 'airport',
    intercity: 'intercity',
    'intercity-transfer': 'intercity',
    charter: 'charter',
    city: 'charter',
    hourly: 'charter',
    'hourly-charter': 'charter',
  };

  function normalizeProduct(p) {
    var s = String(p == null ? 'airport' : p).trim().toLowerCase();
    return PRODUCT_ALIASES[s] || s;
  }

  function round2(n) {
    return Math.round((Number(n) + Number.EPSILON) * 100) / 100;
  }

  function rate(data) {
    var r = parseFloat(data && data.meta && data.meta.usdCnyRate);
    return r > 0 ? r : DEFAULT_USD_CNY_RATE;
  }

  // ==========================================================
  //  超时 / 超里程：2026-11-07 用户确认的新口径
  //  客人不再自己算「超出多少」——表单让他直接填 Google Maps 的
  //  「总里程」和「总行车时长」，系统自动减去套餐已含部分，再计费。
  //  计费块沿用报价单口径：超时 30 分钟一块、超里程 5 公里一块。
  // ==========================================================
  function billingCfg(data) {
    var b = (data && data.meta && data.meta.billing) || {};
    var t = Math.round(Number(b.timeBlockMin) || 30);
    var k = Number(b.kmBlock) || 5;
    return {
      timeBlockMin: t > 0 ? t : 30,
      kmBlock: k > 0 ? k : 5,
    };
  }

  /** 机场 / 城际套餐含多少分钟（标准时长）；报价单未列时长，取 meta 配置 */
  function airportIncludedMinutes(data) {
    var a = (data && data.meta && data.meta.allowances) || {};
    var v = Number(a.airportIncludedMinutes);
    return isFinite(v) && v > 0 ? v : 60;
  }

  /** 向上取整到计费块（不足一块按一块算） */
  function ceilToBlock(value, block) {
    if (!(value > 0)) return 0;
    if (!block) return value;
    return Math.ceil(value / block - 1e-9) * block;
  }

  /** 空字符串 / 非数字 → null（区别于 0） */
  function numOrNull(v) {
    if (v === undefined || v === null) return null;
    var s = String(v).trim();
    if (s === '') return null;
    var n = Number(s);
    return isFinite(n) ? n : null;
  }

  /** 输入上限（防手误/恶意输入算出荒谬价格） */
  function limitsCfg(data) {
    var l = (data && data.meta && data.meta.limits) || {};
    var km = Number(l.maxRouteKm);
    var min = Number(l.maxRouteMinutes);
    return {
      maxRouteKm: km > 0 ? km : 2000,
      maxRouteMinutes: min > 0 ? min : 1440,
    };
  }

  function toUsd(cny, data) {
    return round2(cny / rate(data));
  }

  /** 城市标识归一：去引号/空格/连字符/下划线 */
  function cityKey(city) {
    return String(city == null ? '' : city)
      .trim().toLowerCase()
      .replace(/['\u2019]/g, '')
      .replace(/[\s\-_]/g, '');
  }

  function getCity(data, city) {
    var cities = (data && data.cities) || {};
    var flat = cityKey(city);
    if (cities[flat]) return cities[flat];
    var norm = flat.replace(/[^a-z0-9]/g, '');
    var keys = Object.keys(cities);
    for (var i = 0; i < keys.length; i++) {
      if (keys[i].replace(/[^a-z0-9]/g, '') === norm) return cities[keys[i]];
    }
    return null;
  }

  /**
   * 主报价函数
   * quote(data, opts) → 见文件末尾说明
   */
  function quote(data, opts) {
    opts = opts || {};
    var product = normalizeProduct(opts.product);
    var prod = PRODUCTS[product];

    if (!prod) {
      return { ok: false, error: 'UNKNOWN_PRODUCT', message: 'Unknown product type' };
    }

    var city = getCity(data, opts.city);
    if (!city) {
      return {
        ok: false,
        error: 'CITY_NOT_PRICED',
        message: 'No published price for this city — quote by request',
        quoteRequired: true,
      };
    }

    var vehicleKey = String(opts.vehicle || '').trim();
    var table = city[prod.table] || {};
    var entry = table[vehicleKey];
    if (!entry) {
      return {
        ok: false,
        error: 'VEHICLE_NOT_PRICED',
        message: 'This vehicle is not available in the selected city',
        quoteRequired: true,
        city: city.en,
        product: product,
      };
    }

    var warnings = [];
    var lines = [];
    var pkg = null;
    var includedKm = null;
    var includedMinutes = null;
    var tierMeta = null;

    if (prod.table === 'airport') {
      pkg = entry.pkg;
      includedKm = entry.includedKm || prod.includedKm;
      includedMinutes = airportIncludedMinutes(data);
      tierMeta = {
        key: 'standard',
        name: 'Standard transfer (includes ' + includedKm + ' km + ' + includedMinutes + ' min)',
        hours: null,
        includedKm: includedKm,
        includedMinutes: includedMinutes,
        perMin: entry.perMin,
        perKm: entry.perKm,
      };
      lines.push({
        key: 'package',
        label: vehicleEn(vehicleKey) + ' — ' + tierMeta.name,
        qty: 1, unit: 'trip', unitPrice: pkg, amount: pkg,
      });
    } else {
      var tierKey = String(opts.tier || '').trim();
      var tier = (entry.tiers || {})[tierKey];
      if (!tier) {
        return {
          ok: false,
          error: 'TIER_NOT_PRICED',
          message: 'Please choose a valid package duration',
          quoteRequired: true,
          city: city.en,
          product: product,
          vehicle: vehicleKey,
        };
      }
      pkg = tier.pkg;
      includedKm = tier.includedKm;
      tierMeta = {
        key: tierKey,
        name: tierEn(tier),
        hours: tier.hours,
        includedKm: includedKm,
        includedMinutes: tier.hours ? Math.round(tier.hours * 60) : null,
        perMin: tier.perMin,
        perKm: tier.perKm,
      };
      lines.push({
        key: 'package',
        label: vehicleEn(vehicleKey) + ' — ' + tierMeta.name,
        qty: 1, unit: 'package', unitPrice: pkg, amount: pkg,
      });
    }

    // 超时 / 超里程
    // 客人填「Google Maps 总时长 / 总里程」，系统自动减掉套餐已含部分；
    // 若客人直接填了旧的「extra」字段（兼容），则视为已超出量。
    var billing = billingCfg(data);
    var routeKm = numOrNull(opts.routeKm);
    var routeMinutes = numOrNull(opts.routeMinutes);
    var lim = limitsCfg(data);
    // 超上限 → 视为异常值，不自动计附加费，转人工确认
    // 城际不走超额计费（noOverage），无需限制
    if (!prod.noOverage && routeKm != null && (routeKm < 0 || routeKm > lim.maxRouteKm)) {
      warnings.push('The route distance you entered looks unusual. Our team will confirm the final price with you before you pay.');
      routeKm = null;
    }
    if (!prod.noOverage && routeMinutes != null && (routeMinutes < 0 || routeMinutes > lim.maxRouteMinutes)) {
      warnings.push('The driving time you entered looks unusual. Our team will confirm the final price with you before you pay.');
      routeMinutes = null;
    }
    var rawExtraKm = routeKm != null
      ? Math.max(0, routeKm - (includedKm || 0))
      : Math.max(0, Number(opts.extraKm) || 0);
    var rawExtraMinutes = routeMinutes != null
      ? Math.max(0, routeMinutes - (tierMeta.includedMinutes || 0))
      : Math.max(0, Number(opts.extraMinutes) || 0);

    if (prod.noOverage) {
      rawExtraKm = 0;
      rawExtraMinutes = 0;
      warnings.push('Intercity transfers run at the published rate of the departure city. Long-distance routes are quoted on request — our team confirms the final price with you before you pay.');
    }
    // 按报价单口径取整到计费块
    var billedKm = round2(ceilToBlock(rawExtraKm, billing.kmBlock));
    var billedMinutes = Math.round(ceilToBlock(rawExtraMinutes, billing.timeBlockMin));

    if (billedMinutes > 0) {
      if (tierMeta.perMin == null) {
        warnings.push('Overtime rate is not published for this city/vehicle — our team will confirm it manually');
      } else {
        lines.push({
          key: 'extra_time',
          label: 'Overtime ' + billedMinutes + ' min × ¥' + tierMeta.perMin + '/min',
          qty: billedMinutes, unit: 'min',
          unitPrice: tierMeta.perMin,
          amount: round2(tierMeta.perMin * billedMinutes),
        });
      }
    }

    if (billedKm > 0) {
      if (tierMeta.perKm == null) {
        warnings.push('Extra-distance rate is not published for this city/vehicle — our team will confirm it manually');
      } else {
        lines.push({
          key: 'extra_km',
          label: 'Extra distance ' + billedKm + ' km × ¥' + tierMeta.perKm + '/km',
          qty: billedKm, unit: 'km',
          unitPrice: tierMeta.perKm,
          amount: round2(tierMeta.perKm * billedKm),
        });
      }
    }

    var total = round2(lines.reduce(function (s, l) { return s + l.amount; }, 0));

    // 载客校验
    var pax = parseInt(opts.pax, 10);
    if (isFinite(pax) && pax > 0 && entry.seats && pax > entry.seats) {
      warnings.push('This vehicle takes up to ' + entry.seats + ' passengers, but you selected ' + pax + '. Please upgrade the vehicle or split the group.');
    }

    return {
      ok: true,
      currency: 'CNY',
      usdRate: rate(data),
      city: city.en,
      cityCn: city.cn,
      citySlug: cityKey(opts.city),
      product: product,
      productLabel: prod.label,
      vehicle: vehicleKey,
      vehicleName: vehicleEn(vehicleKey),
      vehicleNameCn: entry.name,
      vehicleSeats: entry.seats,
      vehicleBags: entry.bags,
      tier: tierMeta.key,
      tierName: tierMeta.name,
      includedKm: includedKm,
      includedMinutes: tierMeta.includedMinutes,
      routeKm: routeKm,
      routeMinutes: routeMinutes,
      extraKmRaw: round2(rawExtraKm),
      extraMinutesRaw: round2(rawExtraMinutes),
      billedKm: billedKm,
      billedMinutes: billedMinutes,
      billing: billing,
      lines: lines,
      total: total,
      usd: toUsd(total, data),
      warnings: warnings,
    };
  }

  /** 某城市某产品最低价（城市页起价） */
  function lowestPrice(data, city, product) {
    var c = getCity(data, city);
    if (!c) return null;
    var p = normalizeProduct(product);
    var table = c[(PRODUCTS[p] || PRODUCTS.airport).table] || {};
    var min = null;
    Object.keys(table).forEach(function (vkey) {
      var v = table[vkey];
      if (v.pkg != null && (min === null || v.pkg < min)) min = v.pkg;
      if (v.tiers) {
        Object.keys(v.tiers).forEach(function (tk) {
          var p2 = v.tiers[tk].pkg;
          if (p2 != null && (min === null || p2 < min)) min = p2;
        });
      }
    });
    return min === null ? null : { cny: min, usd: toUsd(min, data) };
  }

  /** 有价城市清单 */
  function listPricedCities(data) {
    var cities = (data && data.cities) || {};
    return Object.keys(cities).map(function (k) {
      var c = cities[k];
      var lo = lowestPrice(data, k, 'airport');
      return {
        slug: k, cn: c.cn, en: c.en, py: c.py || '', prov: c.prov || '', provCn: c.provCn || '',
        fromCny: lo ? lo.cny : null,
        fromUsd: lo ? lo.usd : null,
      };
    }).sort(function (a, b) { return (a.fromCny || 1e9) - (b.fromCny || 1e9); });
  }

  /** 某城市可选矩阵（渲染下拉/卡片用） */
  function cityOptions(data, city) {
    var c = getCity(data, city);
    if (!c) return null;
    return {
      city: c.en,
      cn: c.cn,
      vehicles: (data && data.vehicles) || {},
      charterTiers: (data && data.charterTiers) || [],
      airport: Object.keys(c.airport || {}).map(function (k) {
        var v = c.airport[k];
        return {
          key: k, name: vehicleEn(k), nameCn: v.name, seats: v.seats, bags: v.bags,
          includedKm: v.includedKm, pkg: v.pkg,
          perMin: v.perMin, perKm: v.perKm,
        };
      }),
      charter: Object.keys(c.charter || {}).map(function (k) {
        var v = c.charter[k];
        return {
          key: k, name: vehicleEn(k), nameCn: v.name, seats: v.seats, bags: v.bags,
          tiers: Object.keys(v.tiers || {}).map(function (tk) {
            var t = v.tiers[tk];
            return {
              key: tk, name: tierEn(t), nameCn: t.name, hours: t.hours, includedKm: t.includedKm,
              pkg: t.pkg, perMin: t.perMin, perKm: t.perKm,
            };
          }),
        };
      }),
    };
  }

  return {
    DEFAULT_USD_CNY_RATE: DEFAULT_USD_CNY_RATE,
    PRODUCTS: PRODUCTS,
    normalizeProduct: normalizeProduct,
    cityKey: cityKey,
    getCity: getCity,
    quote: quote,
    lowestPrice: lowestPrice,
    listPricedCities: listPricedCities,
    cityOptions: cityOptions,
    rate: rate,
    toUsd: toUsd,
    round2: round2,
  };
});

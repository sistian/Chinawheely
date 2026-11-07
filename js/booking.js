// ========== Chinawheely Booking v2 (P2) ==========
// 真实报价引擎：数据来自 pricing/pricing.json，算法与后端共用 js/pricing-core.js。
// 前端只做展示与预估；提交后由服务端重算价格（权威值）。

var PRICE_DATA = null;          // pricing.json
var CITY_LIST = [];             // 有价城市
var QUOTE_RESULT = null;        // 最近一次报价
var QUOTE_TOKEN = 0;            // 防竞态
var currentPrice = 0;
var USD_RATE = 7.10;

var el = function (id) { return document.getElementById(id); };

// ============================================================
//  载入价格数据
// ============================================================
function loadPricingData(cb) {
  if (PRICE_DATA) { cb && cb(); return; }
  fetch('/pricing/pricing.json', { cache: 'no-cache' })
    .then(function (r) {
      if (!r.ok) throw new Error('pricing ' + r.status);
      return r.json();
    })
    .then(function (d) {
      PRICE_DATA = d;
      if (d.meta && d.meta.usdCnyRate) USD_RATE = d.meta.usdCnyRate;
      CITY_LIST = window.CWPricing.listPricedCities(d);
      cb && cb();
    })
    .catch(function () {
      // 降级：后端报价接口仍可用，但选项列表需要硬编码兜底
      PRICE_DATA = null;
      cb && cb();
    });
}

// ============================================================
//  城市参数解析
//  站内 CTA 传的是英文名（?city=Beijing / ?city=Guangzhou），不是 slug，
//  所以必须大小写不敏感地同时匹配 slug / 英文名 / 中文名。
// ============================================================
function normalizeCityKey(s) {
  return String(s || '').toLowerCase().replace(/[\s\-_'’.]+/g, '');
}

function resolveCityParam(raw) {
  if (!raw) return null;
  var needle = normalizeCityKey(raw);
  if (!needle) return null;
  var found = null;
  CITY_LIST.forEach(function (c) {
    if (found) return;
    var candidates = [c.slug, c.en, c.cn];
    for (var i = 0; i < candidates.length; i++) {
      if (!candidates[i]) continue;
      if (normalizeCityKey(candidates[i]) === needle) { found = c; return; }
    }
  });
  return found;
}

/**
 * 从来源页推断城市。
 * 全站 3980 个预定链接里有 1992 个（50%）不带 ?city= 参数
 * （每个城市页 hero 区的 "Book Now"、"View Details & Book →" 等都是裸 booking.html），
 * 客户点了要自己从 53 城下拉里挑 —— 这里用 document.referrer 反推。
 */
var NON_CITY_SLUGS = {
  'index': 1, 'booking': 1, 'contact': 1, 'prices': 1, 'manage-order': 1, 'admin': 1,
  'about': 1, 'terms': 1, 'privacy': 1, 'help': 1, 'careers': 1, 'services': 1,
  'cancellation': 1, 'cookies': 1, 'partners': 1, '404': 1, 'seo-swot-analysis': 1
};

function cityFromReferrer() {
  var ref = document.referrer || '';
  if (!ref) return '';
  var u;
  try {
    u = new URL(ref, window.location.origin);
  } catch (e) { return ''; }
  if (u.host !== window.location.host) return '';
  var m = /^\/([a-z0-9_]+)\.html$/i.exec(u.pathname);
  if (!m) return '';
  var slug = m[1].toLowerCase();
  if (NON_CITY_SLUGS[slug]) return '';
  return slug;
}

/** 把 CTA 的城市参数落到下拉框；无公开价的城市走「询价」通道并记住城市名 */
function applyCityParam(raw) {
  var sel = el('city');
  if (!sel) return;

  // 1) 有 ?city= 就用它
  var decoded = '';
  if (raw) {
    decoded = String(raw);
    try { decoded = decodeURIComponent(raw); } catch (e) { /* 保留原值 */ }
    var match = resolveCityParam(decoded);
    if (match) {
      sel.value = match.slug;
      setRequestedCity('');
      return;
    }
    // 没有公开价的城市（286 个 CTA 指向这类城市）：选中「询价」并把城市名带走
    if (sel.querySelector('option[value="other"]')) {
      sel.value = 'other';
      setRequestedCity(decoded);
      return;
    }
  }

  // 2) 没有 ?city= → 从来源页城市反推
  var slug = cityFromReferrer();
  if (!slug) return;
  var match2 = resolveCityParam(slug);
  if (match2) {
    sel.value = match2.slug;
    setRequestedCity('');
    return;
  }
  if (sel.querySelector('option[value="other"]')) {
    sel.value = 'other';
    var guess = slug.replace(/_/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); });
    setRequestedCity(guess);
    refineCityFromReferrerTitle(guess);
  }
}

/**
 * 城市名兜底：从来源页 <title> 取真实城市名。
 * 标题格式固定：「<城市> Airport Transfer & Car Service | Chinawheely」
 * 「Fuzhou (Jiangxi) …」这种重名城市也能拿到准确名字。
 */
function refineCityFromReferrerTitle(fallbackName) {
  var ref = document.referrer || '';
  if (!ref) return;
  try {
    fetch(ref, { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.text() : ''; })
      .then(function (html) {
        if (!html) return;
        var m = /<title[^>]*>([^<]*)<\/title>/i.exec(html);
        if (!m) return;
        var name = decodeHtmlEntities(m[1].split(/[|｜]/)[0])
          .replace(/\s+(Airport|Private Car|Car|Charter|Intercity|Transfer)\b.*$/i, '')
          .trim();
        if (name && name.length <= 40) setRequestedCity(name);
      })
      .catch(function () { /* 失败就用兜底名 */ });
  } catch (e) { /* 忽略 */ }
}

function decodeHtmlEntities(s) {
  return String(s)
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ');
}

function setRequestedCity(name) {
  var f = el('requestedCity');
  if (f) f.value = name || '';
}

// ============================================================
//  距离档 → 超出免费里程的估算公里数
//  与后端 api/booking.js 的 DISTANCE_BAND_KM 保持一致
// ============================================================
var DISTANCE_BAND_KM = { '0-35': 17.5, '35-50': 42.5, '50-80': 65, '80+': 80 };

function derivedExtraKm(band, includedKm) {
  var mid = DISTANCE_BAND_KM[String(band || '').trim()];
  if (mid == null) return 0;
  var inc = Number(includedKm) || 0;
  return Math.max(0, Math.round(mid - inc));
}

/** 距离档变了就把超里程数写进 extraKm 输入框（否则「距离」只是个摆设，不影响报价） */
function syncExtraKmFromDistance() {
  var dr = el('distanceRange');
  var ek = el('extraKm');
  if (!dr || !ek) return;
  if (currentProduct() !== 'airport') return;
  var slug = citySlug();
  if (!slug || slug === 'other' || !PRICE_DATA) return;
  var vkey = selectedVehicleKey();
  if (!vkey) return;
  var o = window.CWPricing.cityOptions(PRICE_DATA, slug);
  if (!o) return;
  var v = o.airport.filter(function (x) { return x.key === vkey; })[0];
  if (!v) return;
  var derived = derivedExtraKm(dr.value, v.includedKm);
  if (derived > 0) ek.value = derived;
}

// ============================================================
//  城市下拉（331 城：热门口岸 + 按省分组）
// ============================================================
function currentCityLabel() {
  var c = el('city');
  if (!c || !c.value || c.value === 'other') return '';
  var o = c.options[c.selectedIndex];
  return o ? (o.textContent || '').split(' — ')[0].trim() : '';
}

function populateCities() {
  var sel = el('city');
  if (!sel) return;
  sel.innerHTML = '<option value="" disabled selected>Select your city</option>';

  if (!CITY_LIST.length) {
    var opt = document.createElement('option');
    opt.value = 'other';
    opt.textContent = 'Other city (quote on request)';
    sel.appendChild(opt);
    renderVehicles();
    return;
  }

  // 分组：按中文拼音首字母 A–Z，组内按全拼排序
  // （pricing.json 每城带 py 字段 = 中文名全拼，无声调）
  var byInitial = {};
  CITY_LIST.forEach(function (c) {
    var py = c.py || (c.en || '').toLowerCase().replace(/[^a-z]/g, '');
    var initial = (py[0] || '#').toUpperCase();
    (byInitial[initial] = byInitial[initial] || []).push(c);
  });
  Object.keys(byInitial).sort().forEach(function (initial) {
    var g = document.createElement('optgroup');
    g.label = initial;
    var list = byInitial[initial].sort(function (a, b) {
      var pa = a.py || (a.en || '').toLowerCase();
      var pb = b.py || (b.en || '').toLowerCase();
      return pa < pb ? -1 : (pa > pb ? 1 : 0);
    });
    list.forEach(function (c) {
      var o = document.createElement('option');
      o.value = c.slug;
      o.textContent = c.en + ' ' + c.cn;
      g.appendChild(o);
    });
    sel.appendChild(g);
  });

  var other = document.createElement('optgroup');
  other.label = 'Other Destinations';
  var oo = document.createElement('option');
  oo.value = 'other';
  oo.textContent = 'Other city / not listed (quote on request)';
  other.appendChild(oo);
  sel.appendChild(other);
}

// ============================================================
//  车型 / 套餐卡片
// ============================================================
function currentProduct() {
  var r = document.querySelector('input[name="product"]:checked');
  return r ? r.value : 'airport';
}

function citySlug() {
  var c = el('city');
  return c ? c.value : '';
}

function renderVehicles() {
  var row = el('vehicleRow');
  if (!row) return;
  var slug = citySlug();

  row.innerHTML = '';

  if (!slug || slug === 'other' || !PRICE_DATA) {
    var p = document.createElement('p');
    p.className = 'text-small';
    p.id = 'vehiclePlaceholder';
    p.textContent = slug === 'other'
      ? 'This destination is quoted on request — submit the form and we will send a fixed quote within 2 hours.'
      : 'Select a city to see available vehicles and packages.';
    row.appendChild(p);
    updateAirportOptions();
    refreshQuote();
    return;
  }

  var opts = window.CWPricing.cityOptions(PRICE_DATA, slug);
  if (!opts) { renderVehiclesFallback(); return; }

  var product = currentProduct();
  var list, tiered;

  if (product === 'charter') {
    list = opts.charter;
    tiered = true;
  } else {
    list = opts.airport;
    tiered = false;
  }

  if (!list.length) {
    var warn = document.createElement('p');
    warn.className = 'text-small';
    warn.textContent = 'No published package for this city and service type — please submit the form for a quote.';
    row.appendChild(warn);
    refreshQuote();
    return;
  }

  list.forEach(function (v) {
    var label = document.createElement('label');
    label.className = 'vehicle-option u-10123434';

    var input = document.createElement('input');
    input.type = 'radio';
    input.name = 'vehicleChoice';
    input.className = 'u-93b8ea5b';
    input.value = v.key;

    var box = document.createElement('div');
    box.className = 'vehicle-option-box u-d57eba37';

    var name = document.createElement('div');
    name.className = 'u-6e844ab5';
    name.textContent = v.name;

    var spec = document.createElement('div');
    spec.className = 'u-6ee65de0';
    spec.textContent = v.seats + ' pax · ' + v.bags + ' bags';

    var price = document.createElement('div');
    price.className = 'vehicle-price u-583db0b0';
    price.setAttribute('data-key', v.key);

    box.appendChild(name);
    box.appendChild(spec);
    box.appendChild(price);
    label.appendChild(input);
    label.appendChild(box);
    row.appendChild(label);

    input.addEventListener('change', function () {
      if (tiered) renderTiers(v);
      syncExtraKmFromDistance();
      refreshQuote();
    });
  });

  // 默认选第一个
  var first = row.querySelector('input[name="vehicleChoice"]');
  if (first) {
    first.checked = true;
    if (tiered) renderTiers(list[0]);
  }

  updateAirportOptions();
  syncExtraKmFromDistance();
  refreshQuote();
}

function renderVehiclesFallback() {
  var row = el('vehicleRow');
  row.innerHTML = '<p class="text-small">Loading vehicles…</p>';
  var slug = citySlug();
  fetchQuoteApi({
    action: 'options', city: slug
  }).then(function (r) {
    if (!r || !r.ok) {
      row.innerHTML = '<p class="text-small">Unable to load packages. Please submit the form for a quote.</p>';
      return;
    }
    row.innerHTML = '';
    var product = currentProduct();
    var list = product === 'charter' ? r.charter : r.airport;
    list.forEach(function (v) {
      var label = document.createElement('label');
      label.className = 'vehicle-option u-10123434';
      var input = document.createElement('input');
      input.type = 'radio';
      input.name = 'vehicleChoice';
      input.className = 'u-93b8ea5b';
      input.value = v.key;
      var box = document.createElement('div');
      box.className = 'vehicle-option-box u-d57eba37';
      var nm = document.createElement('div');
      nm.className = 'u-6e844ab5';
      nm.textContent = v.name;
      var sp = document.createElement('div');
      sp.className = 'u-6ee65de0';
      sp.textContent = v.seats + ' pax · ' + v.bags + ' bags';
      var pr = document.createElement('div');
      pr.className = 'vehicle-price u-583db0b0';
      pr.setAttribute('data-key', v.key);
      box.appendChild(nm); box.appendChild(sp); box.appendChild(pr);
      label.appendChild(input); label.appendChild(box);
      row.appendChild(label);
      input.addEventListener('change', function () { refreshQuote(); });
    });
    var f = row.querySelector('input[name="vehicleChoice"]');
    if (f) f.checked = true;
    updateAirportOptions();
    refreshQuote();
  });
}

// ---- 包车时长档 ----
function renderTiers(vehicle) {
  var holder = el('charterTiers');
  if (!holder) return;
  holder.innerHTML = '';
  if (!vehicle || !vehicle.tiers) return;

  var wrap = document.createElement('div');
  wrap.className = 'form-group u-bc38d4de';
  var lab = document.createElement('label');
  lab.className = 'form-label';
  lab.textContent = 'Package Duration';
  wrap.appendChild(lab);

  var row = document.createElement('div');
  row.className = 'form-row u-b207d191';

  vehicle.tiers.forEach(function (t) {
    var lb = document.createElement('label');
    lb.className = 'service-option u-10123434';
    var inp = document.createElement('input');
    inp.type = 'radio';
    inp.name = 'tierChoice';
    inp.className = 'u-93b8ea5b';
    inp.value = t.key;
    var box = document.createElement('div');
    box.className = 'service-option-box u-267a89a6';
    var n1 = document.createElement('div');
    n1.className = 'u-344f893f';
    n1.textContent = t.name;
    var n2 = document.createElement('div');
    n2.className = 'service-option-note';
    n2.textContent = '¥' + t.pkg + ' · ' + t.hours + 'h / ' + t.includedKm + 'km';
    box.appendChild(n1); box.appendChild(n2);
    lb.appendChild(inp); lb.appendChild(box);
    row.appendChild(lb);
    inp.addEventListener('change', refreshQuote);
  });

  wrap.appendChild(row);
  holder.appendChild(wrap);

  var first = holder.querySelector('input[name="tierChoice"]');
  if (first) first.checked = true;
}

// ============================================================
//  机场下拉（53 城机场库）
// ============================================================
function updateAirportOptions() {
  var sel = el('airport');
  var info = el('airportDistanceInfo');
  var freeText = el('airportFreeText');
  if (!sel) return;
  var cur = sel.value;

  var slug = citySlug();
  var isOther = (slug === 'other');

  // 「其他城市 / 询价」及尚无机场库的城市（331 城全覆盖后部分小城无机场数据）：
  // 改成自由文本填写，否则下拉永远为空、表单永远提交不了
  var noAirportData = !isOther && slug && slug !== 'other' &&
    !(window.AIRPORT_DB && window.AIRPORT_DB[slug]) &&
    !(typeof window.getAirportsForCity === 'function' && (window.getAirportsForCity(slug) || []).length);
  if (isOther || noAirportData) {
    sel.style.display = 'none';
    if (freeText) freeText.style.display = 'block';
    if (info) info.textContent = isOther
      ? 'Tell us which airport you are arriving at — we will confirm the route and price.'
      : 'Type the airport or station name (e.g., ' + (currentCityLabel() || 'your city') + ' Airport) — we will confirm the route.';
    return;
  }
  sel.style.display = '';
  if (freeText) { freeText.style.display = 'none'; freeText.value = ''; }

  while (sel.firstChild) sel.removeChild(sel.firstChild);
  var def = document.createElement('option');
  def.value = '';
  def.disabled = true;
  def.selected = true;
  def.textContent = 'Select airport';
  sel.appendChild(def);

  var list = [];

  if (typeof window.getAirportsForCity === 'function') {
    try { list = window.getAirportsForCity(slug) || []; } catch (e) { list = []; }
  }
  if (!list.length && window.AIRPORT_DB && window.AIRPORT_DB[slug]) {
    list = window.AIRPORT_DB[slug];
  }

  list.forEach(function (a) {
    var o = document.createElement('option');
    o.value = a.code;
    var nm = (typeof window.getAirportName === 'function')
      ? (window.getAirportName(slug, a.code) || a.code) : a.code;
    o.textContent = nm;
    sel.appendChild(o);
  });

  if (cur) sel.value = cur;
  if (info) {
    info.textContent = list.length
      ? (list.length + ' airport(s) serve ' + slug + ' — distance shown is to city centre')
      : 'No airport data for this city yet — our team will confirm the route.';
  }
  updateDistanceDefault();
}

function updateDistanceDefault() {
  var sel = el('airport');
  var dr = el('distanceRange');
  if (!sel || !dr) return;
  var code = sel.value;
  if (!code) return;
  var slug = citySlug();
  var dist = null;
  if (typeof window.getAirportDistance === 'function') {
    dist = window.getAirportDistance(slug, code);
  }
  if (dist == null && window.AIRPORT_DB && window.AIRPORT_DB[slug]) {
    var hit = window.AIRPORT_DB[slug].filter(function (a) { return a.code === code; })[0];
    if (hit) dist = hit.dist;
  }
  if (dist == null) return;
  var v = dist <= 35 ? '0-35' : (dist <= 50 ? '35-50' : (dist <= 80 ? '50-80' : '80+'));
  dr.value = v;
  syncExtraKmFromDistance();
}

// ============================================================
//  报价（前端预估：直接用同一套 pricing-core 算法）
// ============================================================
function selectedVehicleKey() {
  var r = document.querySelector('input[name="vehicleChoice"]:checked');
  return r ? r.value : '';
}

function selectedTierKey() {
  var r = document.querySelector('input[name="tierChoice"]:checked');
  return r ? r.value : '';
}

function refreshQuote() {
  var slug = citySlug();
  var product = currentProduct();
  var vkey = selectedVehicleKey();
  var tkey = selectedTierKey();
  var extraMin = parseInt(el('extraMinutes') ? el('extraMinutes').value : 0, 10) || 0;
  var extraKm = parseInt(el('extraKm') ? el('extraKm').value : 0, 10) || 0;
  var pax = parseInt(el('passengers') ? el('passengers').value : 1, 10) || 1;

  // 隐藏字段同步
  if (el('formProduct')) el('formProduct').value = product;
  if (el('formVehicleKey')) el('formVehicleKey').value = vkey;
  if (el('formTierKey')) el('formTierKey').value = tkey;
  if (el('formExtraMinutes')) el('formExtraMinutes').value = extraMin;
  if (el('formExtraKm')) el('formExtraKm').value = extraKm;

  // 切换到非包车产品时，清理残留的时长档选择（避免提交脏数据）
  if (product !== 'charter') {
    var staleTiers = document.querySelectorAll('input[name="tierChoice"]');
    staleTiers.forEach(function (t) { t.checked = false; });
    var tierHolder = el('charterTiers');
    if (tierHolder) tierHolder.innerHTML = '';
    tkey = '';
    if (el('formTierKey')) el('formTierKey').value = '';
  }

  // 显示/隐藏分组
  var af = el('airportFields');
  var cf = el('charterFields');
  var ic = el('intercityFields');
  var og = el('overtimeGroup');
  if (af) af.style.display = product === 'airport' ? 'block' : 'none';
  if (cf) cf.style.display = product === 'charter' ? 'block' : 'none';
  if (ic) ic.style.display = product === 'intercity' ? 'block' : 'none';

  // 隐藏无价组合的超时项
  var hasSurcharge = false;
  if (PRICE_DATA) {
    var opts = window.CWPricing.cityOptions(PRICE_DATA, slug);
    if (opts) {
      var v = product === 'charter'
        ? opts.charter.filter(function (x) { return x.key === vkey; })[0]
        : opts.airport.filter(function (x) { return x.key === vkey; })[0];
      if (v) {
        if (product === 'charter') {
          var t = v.tiers.filter(function (x) { return x.key === tkey; })[0];
          hasSurcharge = !!(t && t.perMin != null && t.perKm != null);
        } else {
          hasSurcharge = (v.perMin != null && v.perKm != null);
        }
      }
    }
  }
  if (og) og.style.display = hasSurcharge ? 'block' : 'none';
  if (!hasSurcharge) {
    var hint = el('overtimeHint');
    if (hint && slug && slug !== 'other' && vkey) {
      hint.textContent = 'Overage rates are not published for this city and vehicle — our team will confirm the final amount.';
    }
  } else {
    var hint2 = el('overtimeHint');
    if (hint2) hint2.textContent = 'Charged at the published rate for your city and vehicle. Final settlement is confirmed by our team.';
  }

  // 容量提示
  var capHint = el('capacityHint');
  if (capHint && PRICE_DATA && vkey) {
    var o2 = window.CWPricing.cityOptions(PRICE_DATA, slug);
    if (o2) {
      var all = o2.airport.concat(o2.charter);
      var vv = all.filter(function (x) { return x.key === vkey; })[0];
      if (vv) {
        capHint.textContent = pax > vv.seats
          ? '⚠️ ' + vv.name + ' takes up to ' + vv.seats + ' passengers — you selected ' + pax + '.'
          : vv.name + ': up to ' + vv.seats + ' passengers, ' + vv.bags + ' large bags.';
      }
    }
  }

  // 报价
  if (!slug || slug === 'other' || !vkey || !PRICE_DATA) {
    QUOTE_RESULT = null;
    currentPrice = 0;
    renderQuotePanel(null);
    updateVehicleLabels(null);
    return;
  }

  var q = window.CWPricing.quote(PRICE_DATA, {
    city: slug,
    product: product,
    vehicle: vkey,
    tier: tkey,
    extraMinutes: extraMin,
    extraKm: extraKm,
    pax: pax
  });

  if (!q.ok) {
    QUOTE_RESULT = null;
    currentPrice = 0;
    renderQuotePanel(null);
    updateVehicleLabels(null);
    return;
  }

  QUOTE_RESULT = q;
  currentPrice = q.total;
  renderQuotePanel(q);
  updateVehicleLabels(q);
}

function updateVehicleLabels(q) {
  var els = document.querySelectorAll('.vehicle-price');
  els.forEach(function (elx) {
    var key = elx.getAttribute('data-key');
    if (!PRICE_DATA) { elx.textContent = ''; return; }
    var opts = window.CWPricing.cityOptions(PRICE_DATA, citySlug());
    if (!opts) { elx.textContent = ''; return; }
    var product = currentProduct();
    var list = product === 'charter' ? opts.charter : opts.airport;
    var v = list.filter(function (x) { return x.key === key; })[0];
    if (!v) { elx.textContent = ''; return; }
    if (product === 'charter') {
      var min = null;
      v.tiers.forEach(function (t) { if (min === null || t.pkg < min) min = t.pkg; });
      elx.textContent = 'From ¥' + min;
    } else {
      elx.textContent = '¥' + v.pkg;
    }
  });
}

// ============================================================
//  报价面板
// ============================================================
function renderQuotePanel(q) {
  var panel = el('quotePanel');
  var rows = el('quoteRows');
  var totalCny = el('quoteTotalCny');
  var totalUsd = el('quoteTotalUsd');
  var note = el('quoteNote');
  var warnBox = el('quoteWarnings');

  if (!panel) return;

  if (!q) {
    if (rows) rows.innerHTML = '<div class="quote-row"><span>Select a city, vehicle and package to see your price</span></div>';
    if (totalCny) totalCny.textContent = '—';
    if (totalUsd) totalUsd.textContent = '—';
    if (note) note.textContent = '';
    if (warnBox) warnBox.innerHTML = '';
    return;
  }

  if (rows) {
    rows.innerHTML = '';
    q.lines.forEach(function (l) {
      var r = document.createElement('div');
      r.className = 'quote-row';
      var a = document.createElement('span');
      a.textContent = l.label;
      var b = document.createElement('span');
      b.className = 'quote-amount';
      b.textContent = '¥' + l.amount;
      r.appendChild(a); r.appendChild(b);
      rows.appendChild(r);
    });
  }

  if (totalCny) totalCny.textContent = '¥' + q.total;
  if (totalUsd) totalUsd.textContent = '≈ $' + q.usd;
  if (note) {
    note.textContent = q.city + ' · ' + q.vehicleName +
      (product_tier_name(q));
  }
  if (warnBox) {
    warnBox.innerHTML = '';
    (q.warnings || []).forEach(function (w) {
      var d = document.createElement('div');
      d.className = 'quote-warning';
      d.textContent = '⚠️ ' + w;
      warnBox.appendChild(d);
    });
  }

  // 同步隐藏字段
  if (el('formTotalCny')) el('formTotalCny').value = q.total;
  if (el('formTotalUsd')) el('formTotalUsd').value = q.usd;
  if (el('formBreakdown')) {
    el('formBreakdown').value = JSON.stringify({
      lines: q.lines, total: q.total, usd: q.usd,
      vehicle: q.vehicle, tier: q.tier, includedKm: q.includedKm
    });
  }
}

function product_tier_name(q) {
  return q.tier && q.tier !== 'standard' ? ' · ' + q.tierName : '';
}

// ============================================================
//  后端报价 API（降级路径 / 最终校验）
// ============================================================
function fetchQuoteApi(payload) {
  return fetch('https://api.chinawheely.com/api/quote', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }).then(function (r) { return r.json(); })
    .catch(function () { return { ok: false, error: 'NETWORK' }; });
}

// ============================================================
//  摘要 + 支付弹窗
// ============================================================
function updateSummary() {
  var sService = el('summaryService');
  var sRoute = el('summaryRoute');
  var sDateTime = el('summaryDateTime');
  var sVehicle = el('summaryVehicle');
  var sPassengers = el('summaryPassengers');
  var sPrice = el('summaryPrice');
  var sPriceCny = el('summaryPriceCny');
  var sCity = el('summaryCity');
  var sExtras = el('summaryExtras');

  var product = currentProduct();
  var labels = {
    airport: 'Airport Transfer',
    charter: 'Hourly Charter',
    intercity: 'Intercity Transfer'
  };
  if (sService) sService.textContent = labels[product] || product;

  var slug = citySlug();
  var cityName = '-';
  if (slug && slug !== 'other' && PRICE_DATA) {
    var o = window.CWPricing.cityOptions(PRICE_DATA, slug);
    if (o) cityName = o.city;
  } else if (slug === 'other') {
    var req = el('requestedCity');
    cityName = (req && req.value) ? req.value : 'Other city';
  }
  if (sCity) sCity.textContent = cityName;
  if (sRoute) {
    var route = '';
    if (product === 'airport') {
      var ap = el('airport') ? el('airport').value : '';
      var dir = el('transferDirection') ? el('transferDirection').value : '';
      var ha = el('hotelAddress') ? el('hotelAddress').value : '';
      route = [ap, dir === 'airport-to-hotel' ? '→ Hotel' : (dir === 'hotel-to-airport' ? 'Hotel →' : ''), ha].filter(Boolean).join(' ');
    } else if (product === 'charter') {
      var cr = el('charterRoute') ? el('charterRoute').value : '';
      route = cr || 'Charter';
    } else {
      var fc = el('fromCity') ? el('fromCity').value : '';
      var tc = el('toCity') ? el('toCity').value : '';
      route = (fc || '—') + ' → ' + (tc || '—');
    }
    sRoute.textContent = cityName + (route ? ' — ' + route : '');
  }

  var d = el('date') ? el('date').value : '';
  var t = el('time') ? el('time').value : '';
  if (sDateTime) sDateTime.textContent = (d && t) ? (d + ' ' + t) : '-';

  var vname = '';
  if (QUOTE_RESULT) vname = QUOTE_RESULT.vehicleName;
  if (sVehicle) sVehicle.textContent = vname || '-';

  var pax = el('passengers') ? el('passengers').value : '-';
  if (sPassengers) sPassengers.textContent = pax;

  var extras = [];
  document.querySelectorAll('input[name="extras"]').forEach(function (cb) {
    if (!cb.checked) return;
    var labels = { childseat: 'Child seat', meetgreet: 'Meet & greet', wifi: 'Free Wi-Fi' };
    extras.push(labels[cb.value] || cb.value);
  });
  if (sExtras) sExtras.textContent = extras.length ? extras.join(', ') : '-';

  if (sPrice) sPrice.textContent = QUOTE_RESULT ? ('¥' + QUOTE_RESULT.total) : '-';
  if (sPriceCny) sPriceCny.textContent = QUOTE_RESULT ? ('≈ $' + QUOTE_RESULT.usd) : '';
}

// ============================================================
//  提交：先建单 → 再展示付款码 → 客户付款
//  （旧流程是先付款再提交：客户付完钱关掉页面，钱就打了水漂，还没有订单）
// ============================================================
var SUBMITTING = false;
var ORDER_RESULT = null;

/** 把提交按钮切成忙碌状态 */
function setSubmitBusy(busy) {
  var buttons = document.querySelectorAll('[data-action="submit-booking"]');
  buttons.forEach(function (b) {
    b.disabled = busy;
    if (busy) b.textContent = 'Creating your order…';
    else b.textContent = 'I\'ve Made the Payment — View My Booking';
  });
  var cont = document.querySelector('#bookingForm button[type="submit"]');
  if (cont) {
    cont.disabled = busy;
    cont.textContent = busy ? 'Creating your order… (usually a few seconds)' : 'Continue to Payment';
  }
}

/** 创建订单（fetch + JSON 响应），成功后展示付款码 */
function createOrder() {
  if (SUBMITTING) return;
  var form = el('bookingForm');
  if (!form) return;

  SUBMITTING = true;
  setSubmitBusy(true);

  fetch(form.action, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      // 用 urlencoded 而不是 FormData（multipart）：与原生表单提交完全一致，
      // 也省掉一次 CORS 预检
      'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    },
    body: new URLSearchParams(new FormData(form)).toString()
  }).then(function (r) {
    return r.json().then(function (j) { return { status: r.status, json: j }; })
      .catch(function () { return { status: r.status, json: null }; });
  }).then(function (res) {
    SUBMITTING = false;
    setSubmitBusy(false);
    var j = res.json;
    if (!j || j.ok !== true) {
      var msg = (j && (j.message || j.error)) || 'Booking failed. Please try again.';
      showBookingErrorMsg(msg);
      return;
    }
    ORDER_RESULT = j;
    openPaymentModal(j);
  }).catch(function () {
    SUBMITTING = false;
    setSubmitBusy(false);
    showBookingErrorMsg('Network error — your booking was not submitted. Please check your connection, or message us on WhatsApp +86 155 2777 1775.');
  });
}

/** 把错误同时显示为横幅 + toast */
function showBookingErrorMsg(msg) {
  var banner = el('bookingError');
  if (banner) {
    banner.textContent = msg;
    banner.style.display = 'block';
    banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  if (typeof showToast === 'function') showToast(msg, 'error');
}

/**
 * 「我已付款」→ 去感谢页。
 * 订单在打开付款弹窗之前就已经建好了，这里只负责带客户去看订单详情 + 付款说明。
 */
function submitBooking() {
  if (SUBMITTING) return;
  if (!ORDER_RESULT) { createOrder(); return; }
  // 用后端给的 redirect（带 ref / 金额 / 自助管理 token）
  var target = ORDER_RESULT.redirect;
  if (!target) {
    var ref = ORDER_RESULT.ref ? ('?ref=' + encodeURIComponent(ORDER_RESULT.ref)) : '';
    var amt = ORDER_RESULT.amountCny ? ('&amount=' + encodeURIComponent(String(ORDER_RESULT.amountCny))) : '';
    target = 'thank-you.html' + ref + amt;
  }
  window.location.href = target + (target.indexOf('#') >= 0 ? '' : '#payment');
}

/** 提交前把摘要信息同步到隐藏字段（弹窗此时还没开，直接从表单+报价算） */
function syncHiddenFields() {
  var formPaymentMethod = el('paymentMethod');
  if (formPaymentMethod) {
    var alipayTab = el('tab-alipay');
    formPaymentMethod.value = (alipayTab && alipayTab.classList.contains('active')) ? 'alipay' : 'paypal';
  }
  var formRouteSummary = el('formRouteSummary');
  if (formRouteSummary) formRouteSummary.value = buildRouteSummary();
  var formServiceType = el('formServiceType');
  if (formServiceType) formServiceType.value = productLabel(currentProduct());
  var formVehicleLabel = el('formVehicleLabel');
  if (formVehicleLabel) {
    var pax = el('passengers') ? el('passengers').value : '';
    formVehicleLabel.value = (QUOTE_RESULT ? QUOTE_RESULT.vehicleName : '') +
      (pax ? ' (' + pax + ' pax)' : '');
  }
}

// ---- 支付弹窗：PayPal / 支付宝 切换 + 关闭 ----
// scripts.js 的全局委托会调用这两个函数，之前全站未定义，导致：
// × 关闭按钮无反应（客户被卡在弹窗里）、支付宝标签页根本点不开。
function switchPaymentTab(tab) {
  var target = (tab === 'alipay') ? 'alipay' : 'paypal';
  document.querySelectorAll('.payment-tab').forEach(function (t) {
    var on = (t.getAttribute('data-tab') === target);
    t.classList.toggle('active', on);
    t.setAttribute('aria-selected', on ? 'true' : 'false');
  });
  document.querySelectorAll('.payment-tab-content').forEach(function (c) {
    var on = (c.id === 'tab-' + target);
    c.classList.toggle('active', on);
    c.style.display = on ? 'block' : 'none';
  });
  var pm = el('paymentMethod');
  if (pm) pm.value = target;
}

function closePaymentModal() {
  var modal = el('paymentModal');
  if (modal) {
    modal.classList.remove('active');
    modal.style.display = 'none';
  }
  document.body.classList.remove('modal-open');
}

// ---- 表单提交 → 校验 → 打开支付弹窗 ----
function handleFormSubmit(e) {
  e.preventDefault();
  var form = el('bookingForm');
  if (!form) return;

  var product = currentProduct();

  // 基本必填
  var requiredIds = ['city', 'firstName', 'lastName', 'email', 'phone', 'date', 'time'];
  var slugNow = citySlug();
  var isOtherCity = (slugNow === 'other');
  if (product === 'airport') {
    requiredIds.push('transferDirection', 'hotelAddress', 'distanceRange');
    // 「其他城市」或无机场库的城市（自由文本填机场）；否则下拉永远为空、提交被卡死
    var hasAirportDb = slugNow && slugNow !== 'other' &&
      ((window.AIRPORT_DB && window.AIRPORT_DB[slugNow]) ||
       (typeof window.getAirportsForCity === 'function' && (window.getAirportsForCity(slugNow) || []).length));
    if (isOtherCity || !hasAirportDb) requiredIds.push('airportFreeText');
    else requiredIds.push('airport');
  } else if (product === 'charter') {
    requiredIds.push('charterRoute');
  }
  for (var i = 0; i < requiredIds.length; i++) {
    var f = el(requiredIds[i]);
    if (f && !f.value) {
      if (typeof showToast === 'function') {
        showToast('Please complete: ' + (f.getAttribute('aria-label') || requiredIds[i]), 'error');
      }
      f.focus();
      return;
    }
  }

  // 邮箱格式
  var email = el('email');
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
    if (typeof showToast === 'function') showToast('Please enter a valid email address', 'error');
    email.focus();
    return;
  }

  // 有价组合必须有报价
  if (slugIsPriced() && !QUOTE_RESULT) {
    if (typeof showToast === 'function') {
      showToast('Please select a vehicle and package to see your price', 'error');
    }
    return;
  }

  // 先把摘要写进隐藏字段，然后创建订单（订单建好后再弹付款码）
  syncHiddenFields();
  createOrder();
}

/** 展示付款弹窗：订单号 + 金额 + 收款码 */
function openPaymentModal(orderResult) {
  var product = currentProduct();
  var slug = citySlug();
  var cityName = '-';
  if (PRICE_DATA && slug && slug !== 'other') {
    var o = window.CWPricing.cityOptions(PRICE_DATA, slug);
    if (o) cityName = o.city;
  } else if (slug === 'other') {
    cityName = 'Other city (quoted on request)';
  }
  setModalText('modalService', productLabel(product));
  setModalText('modalCity', cityName);
  setModalText('modalRoute', buildRouteSummary());
  setModalText('modalDateTime', (el('date').value || '') + ' ' + (el('time').value || ''));
  setModalText('modalVehicle', QUOTE_RESULT ? QUOTE_RESULT.vehicleName : 'To be confirmed');
  setModalText('modalPassengers', el('passengers').value);

  var mPrice = el('modalPrice');
  if (mPrice) mPrice.textContent = QUOTE_RESULT ? ('¥' + QUOTE_RESULT.total) : 'On request';
  var mUsd = el('modalPriceUsd');
  if (mUsd) mUsd.textContent = QUOTE_RESULT ? ('≈ $' + QUOTE_RESULT.usd) : '—';
  var mCny = el('modalPriceCny');
  if (mCny) mCny.textContent = QUOTE_RESULT ? QUOTE_RESULT.total : '—';

  // 扫码金额提示（PayPal / 支付宝都是扫码后自己输金额）
  var amtTxt = QUOTE_RESULT ? ('¥' + QUOTE_RESULT.total + ' CNY') : 'the quoted amount';
  ['modalPayAmountCny', 'modalPayAmountCnyAlipay'].forEach(function (id) {
    var e = el(id);
    if (e) e.textContent = amtTxt;
  });

  // 订单号：客户付款后要报这个号
  var mRef = el('modalOrderRef');
  if (mRef) {
    mRef.textContent = (orderResult && orderResult.ref) ? orderResult.ref : '';
    var wrap = el('modalOrderRefWrap');
    if (wrap) wrap.style.display = (orderResult && orderResult.ref) ? 'flex' : 'none';
  }

  var modal = el('paymentModal');
  if (modal) {
    modal.style.display = 'flex';
    modal.classList.add('active');
    document.body.classList.add('modal-open');
  }
}

function slugIsPriced() {
  var slug = citySlug();
  return !!(slug && slug !== 'other' && PRICE_DATA);
}

function productLabel(p) {
  return { airport: 'Airport Transfer', charter: 'Hourly Charter', intercity: 'Intercity Transfer' }[p] || p;
}

function buildRouteSummary() {
  var product = currentProduct();
  var parts = [];
  if (product === 'airport') {
    var ap = el('airport') ? el('airport').value : '';
    if (ap) {
      var apEl = el('airport');
      parts.push(apEl.options[apEl.selectedIndex] ? apEl.options[apEl.selectedIndex].text : ap);
    } else {
      // 无机场库的城市用自由文本填机场，摘要里也要带上（否则路由信息只剩目的地）
      var ft = el('airportFreeText') ? el('airportFreeText').value.trim() : '';
      if (ft) parts.push(ft);
    }
    var dir = el('transferDirection') ? el('transferDirection').value : '';
    if (dir === 'airport-to-hotel') parts.push('→ Hotel');
    if (dir === 'hotel-to-airport') parts.push('Hotel →');
    var ha = el('hotelAddress') ? el('hotelAddress').value : '';
    if (ha) parts.push(ha);
  } else if (product === 'charter') {
    var cr = el('charterRoute') ? el('charterRoute').value : '';
    if (cr) parts.push(cr);
    if (QUOTE_RESULT && QUOTE_RESULT.tierName) parts.push(QUOTE_RESULT.tierName);
  } else {
    var fc = el('fromCity') ? el('fromCity').value : '';
    var tc = el('toCity') ? el('toCity').value : '';
    if (fc) parts.push(fc);
    if (tc) parts.push('→ ' + tc);
  }
  return parts.join(' ');
}

function setModalText(id, text) {
  var e = el(id);
  if (e) e.textContent = text || '-';
}

// ============================================================
//  初始化
// ============================================================
function initBooking() {
  loadPricingData(function () {
    populateCities();
    var params = new URLSearchParams(window.location.search);
    applyCityParam(params.get('city'));
    renderVehicles();
    updateSummary();
  });

  var citySel = el('city');
  if (citySel) citySel.addEventListener('change', function () {
    renderVehicles();
    updateSummary();
  });

  document.querySelectorAll('input[name="product"]').forEach(function (r) {
    r.addEventListener('change', function () {
      renderVehicles();
      updateSummary();
    });
  });

  ['extraMinutes', 'extraKm', 'passengers', 'date', 'time',
    'transferDirection', 'hotelAddress', 'charterRoute', 'fromCity', 'toCity'
  ].forEach(function (id) {
    var e = el(id);
    if (!e) return;
    e.addEventListener('change', function () { refreshQuote(); updateSummary(); });
    if (e.tagName === 'INPUT' && e.type === 'text') {
      e.addEventListener('input', function () { updateSummary(); });
    }
  });

  // 机场变化 → 先重算默认距离档，再刷报价。
  // 之前 airport 的 change 只调 refreshQuote/updateSummary，updateDistanceDefault()
  // 只在重建下拉时调用一次，导致距离档永远是空的（客户只能手填，且填小了会少算钱）。
  var airportSel = el('airport');
  if (airportSel) {
    airportSel.addEventListener('change', function () {
      updateDistanceDefault();
      refreshQuote();
      updateSummary();
    });
  }

  // 距离档变了 → 重算超里程并刷新报价
  var dr = el('distanceRange');
  if (dr) {
    dr.addEventListener('change', function () {
      syncExtraKmFromDistance();
      refreshQuote();
      updateSummary();
    });
  }
  var freeText = el('airportFreeText');
  if (freeText) {
    freeText.addEventListener('input', function () { updateSummary(); });
  }
  document.querySelectorAll('input[name="extras"]').forEach(function (cb) {
    cb.addEventListener('change', updateSummary);
  });

  // 默认日期 = 明天（用本地日期，不要用 toISOString 的 UTC 日期，否则凌晨会选到昨天）
  var tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  var dateEl = el('date');
  if (dateEl && !dateEl.value) dateEl.value = localDateString(tomorrow);

  // 表单提交 → 支付弹窗
  var bf = el('bookingForm');
  if (bf) bf.addEventListener('submit', handleFormSubmit);

  // 注意：不再在这里给 [data-action="submit-booking"] 绑 click。
  // scripts.js 已有全局委托（handleAction → submitBooking），
  // 两边都绑会导致一次点击提交两次（重复下单 / 重复邮件）。

  // 支付弹窗里的标签页切换
  document.querySelectorAll('.payment-tab').forEach(function (t) {
    t.addEventListener('click', function () { switchPaymentTab(t.getAttribute('data-tab')); });
  });

  // 从后端带回来的错误（?error=...）
  showBookingError();
}

function localDateString(d) {
  var m = d.getMonth() + 1;
  var day = d.getDate();
  return d.getFullYear() + '-' + (m < 10 ? '0' + m : m) + '-' + (day < 10 ? '0' + day : day);
}

/** 服务端校验失败 / 邮件服务不可用时，把原因告诉客户 */
function showBookingError() {
  var params = new URLSearchParams(window.location.search);
  var code = params.get('error');
  if (!code) return;
  var known = {
    missing_firstName: 'Please enter your first name.',
    missing_lastName: 'Please enter your last name.',
    missing_email: 'Please enter your email address.',
    missing_phone: 'Please enter your phone number.',
    invalid_email: 'Please enter a valid email address.',
    invalid_date: 'Please pick a valid pick-up date.',
    past_date: 'The pick-up date cannot be in the past.',
    mail_unavailable: 'Booking service is temporarily unavailable. Please try again shortly, or message us on WhatsApp +86 155 2777 1775.'
  };
  var msg = params.get('msg') || known[code] || 'Something went wrong. Please try again.';
  if (typeof showToast === 'function') showToast(msg, 'error');
  var banner = el('bookingError');
  if (banner) {
    banner.textContent = msg;
    banner.style.display = 'block';
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initBooking);
} else {
  initBooking();
}

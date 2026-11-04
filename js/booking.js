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
//  城市下拉
// ============================================================
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

  // 分组：热门入境口岸 / 其他有价城市
  var hot = ['shanghai', 'beijing', 'guangzhou', 'shenzhen', 'chengdu',
    'hangzhou', 'xian', 'wuhan'];
  var g1 = document.createElement('optgroup');
  g1.label = 'Top Entry Points (Most Popular)';
  var g2 = document.createElement('optgroup');
  g2.label = 'Cities with Published Prices';

  CITY_LIST.forEach(function (c) {
    var o = document.createElement('option');
    o.value = c.slug;
    o.textContent = c.cn + ' ' + c.en + ' — From ¥' + c.fromCny;
    if (hot.indexOf(c.slug) >= 0) g1.appendChild(o);
    else g2.appendChild(o);
  });

  var other = document.createElement('optgroup');
  other.label = 'Other Destinations';
  var oo = document.createElement('option');
  oo.value = 'other';
  oo.textContent = 'Other city / not listed (quote on request)';
  other.appendChild(oo);

  sel.appendChild(g1);
  sel.appendChild(g2);
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
  if (!sel) return;
  var cur = sel.value;

  while (sel.firstChild) sel.removeChild(sel.firstChild);
  var def = document.createElement('option');
  def.value = '';
  def.disabled = true;
  def.selected = true;
  def.textContent = 'Select airport';
  sel.appendChild(def);

  var slug = citySlug();
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
    cityName = 'Other city';
  }
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

  if (sPrice) sPrice.textContent = QUOTE_RESULT ? ('¥' + QUOTE_RESULT.total) : '-';
  if (sPriceCny) sPriceCny.textContent = QUOTE_RESULT ? ('≈ $' + QUOTE_RESULT.usd) : '';
}

// ============================================================
//  提交：先走支付弹窗，再由弹窗按钮真正提交
// ============================================================
function submitBooking() {
  var formPrice = el('formPrice');
  if (formPrice) formPrice.value = QUOTE_RESULT ? ('¥' + QUOTE_RESULT.total + ' CNY') : '';

  var formRouteSummary = el('formRouteSummary');
  if (formRouteSummary) {
    var modalRoute = el('modalRoute');
    formRouteSummary.value = modalRoute ? modalRoute.textContent : '';
  }

  var formServiceType = el('formServiceType');
  if (formServiceType) {
    var modalService = el('modalService');
    formServiceType.value = modalService ? modalService.textContent : '';
  }

  var formVehicleLabel = el('formVehicleLabel');
  if (formVehicleLabel) {
    var modalVehicle = el('modalVehicle');
    var modalPassengers = el('modalPassengers');
    formVehicleLabel.value = (modalVehicle ? modalVehicle.textContent : '') +
      (modalPassengers ? ' (' + modalPassengers.textContent + ' pax)' : '');
  }

  var form = el('bookingForm');
  if (form) form.submit();
}

// ---- 表单提交 → 校验 → 打开支付弹窗 ----
function handleFormSubmit(e) {
  e.preventDefault();
  var form = el('bookingForm');
  if (!form) return;

  var product = currentProduct();

  // 基本必填
  var requiredIds = ['city', 'firstName', 'lastName', 'email', 'phone', 'date', 'time'];
  if (product === 'airport') {
    requiredIds.push('airport', 'transferDirection', 'hotelAddress', 'distanceRange');
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

  // 填支付弹窗
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
    var pre = params.get('city');
    if (pre) {
      var sel = el('city');
      if (sel) {
        var match = CITY_LIST.filter(function (c) { return c.slug === pre; })[0];
        if (match) sel.value = pre;
      }
    }
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

  ['extraMinutes', 'extraKm', 'passengers', 'date', 'time', 'airport',
    'transferDirection', 'hotelAddress', 'charterRoute', 'fromCity', 'toCity'
  ].forEach(function (id) {
    var e = el(id);
    if (!e) return;
    e.addEventListener('change', function () { refreshQuote(); updateSummary(); });
    if (e.tagName === 'INPUT' && e.type === 'text') {
      e.addEventListener('input', function () { updateSummary(); });
    }
  });

  // 默认日期 = 明天
  var tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  var dateEl = el('date');
  if (dateEl && !dateEl.value) dateEl.value = tomorrow.toISOString().split('T')[0];

  // 表单提交 → 支付弹窗
  var bf = el('bookingForm');
  if (bf) bf.addEventListener('submit', handleFormSubmit);

  // 支付弹窗里的确认按钮 → 真正提交
  document.querySelectorAll('[data-action="submit-booking"]').forEach(function (b) {
    b.addEventListener('click', function () {
      if (typeof window.ChinawheelySecurity !== 'undefined' &&
        window.ChinawheelySecurity && window.ChinawheelySecurity.honeypotCheck) {
        // 安全模块负责 honeypot / 时长校验
      }
      submitBooking();
    });
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initBooking);
} else {
  initBooking();
}

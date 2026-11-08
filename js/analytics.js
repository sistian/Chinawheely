/**
 * Chinawheely — 流量埋点模块（集中式）
 *
 * 双通道：
 *   A) GA4（可选）—— 把下方 GA_MEASUREMENT_ID 填成 'G-XXXXXXXXXX' 即启用；
 *   B) 自建分析（默认开启）—— 事件 POST 到自建接口 api/analytics，落到 Supabase cw_analytics，
 *      后台 admin.html 的「数据」Tab 查看。不依赖任何 Google 账号。
 *
 * 事件设计（对齐业务漏斗，GA4 与自建口径完全一致）：
 *   - page_view            自动（页面加载）
 *   - booking_start       进入 booking 表单
 *   - booking_submit      提交订单表单（成功）
 *   - booking_error       提交失败
 *   - contact_submit      提交询盘表单
 *   - quote_request       请求报价
 *   - whatsapp_click      点击 WhatsApp（移动端主转化）
 *   - phone_click         点击电话
 *   - city_card_click     首页城市卡片
 *   - price_cta_click     价格区块 CTA
 *   - nav_click           导航点击（带菜单名）
 *
 * 隐私：只上报事件维度与业务维度（产品/车型/时长），不采集姓名、邮箱、电话等个人信息；
 *       后端 api/analytics.js 还会再过滤一遍 PII 键。任何异常都静默吞掉，绝不影响页面。
 */
(function () {
  'use strict';

  // ★↓↓ GA4 ID（留空则只走自建分析） ★↓↓
  // Chinawheely 专属数据流（GA4 属性 563169774 / Web 数据流 16296752182）
  var GA_MEASUREMENT_ID = 'G-LBTYX5G1HW';

  // 自建分析接口（与 booking.html / contact.html 使用同一后端域名）
  var ANALYTICS_API = 'https://api.chinawheely.com/api/analytics';

  window.CWG_GA_ID = GA_MEASUREMENT_ID;
  var GA_ENABLED = /^G-[A-Z0-9]{6,}$/i.test(GA_MEASUREMENT_ID);

  // ---------- 加载 gtag.js ----------
  if (GA_ENABLED) {
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    window.gtag = gtag;
    gtag('js', new Date());
    gtag('config', GA_MEASUREMENT_ID, { send_page_view: true });
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_MEASUREMENT_ID;
    document.head.appendChild(s);
  }

  // ---------- 允许进入 props 的业务维度白名单（其余一律丢弃） ----------
  var PROP_ALLOWED = {
    city: 1, form_id: 1, service_type: 1, vehicle_type: 1,
    product: 1, vehicle: 1, tier: 1, hours: 1, label: 1,
    endpoint: 1, status: 1, reason: 1, form: 1,
    utm_source: 1, utm_medium: 1, utm_campaign: 1, landing_page: 1
  };

  // ---------- 会话 id（sessionStorage；隐私模式下降级为内存随机值） ----------
  var SESSION_KEY = 'cw_sid';
  var memSessionId = null;

  function randomId() {
    try {
      if (window.crypto && window.crypto.getRandomValues) {
        var buf = new Uint8Array(16);
        window.crypto.getRandomValues(buf);
        var hex = '';
        for (var i = 0; i < buf.length; i++) {
          hex += (buf[i] + 0x100).toString(16).slice(1);
        }
        return hex;
      }
    } catch (e) { /* ignore */ }
    return Math.random().toString(36).slice(2) + Date.now().toString(36);
  }

  function sessionId() {
    if (memSessionId) return memSessionId;
    var id = null;
    try {
      id = window.sessionStorage.getItem(SESSION_KEY);
      if (!id) {
        id = randomId();
        window.sessionStorage.setItem(SESSION_KEY, id);
      }
    } catch (e) {
      // 隐私模式 / sessionStorage 不可用 → 内存态
      id = memSessionId || (memSessionId = randomId());
    }
    if (!id) id = memSessionId = randomId();
    return id;
  }

  /** 从当前 URL 解析城市 slug（用于给事件打城市维度） */
  function currentCity() {
    var m = window.location.pathname.match(/\/([a-z0-9_-]+)\.html$/i);
    if (m && m[1] && m[1] !== 'index') { return m[1]; }
    return document.body.getAttribute('data-city') || '';
  }

  /** 从表单收集 UTM / 落地页维度 */
  function sessionContext() {
    try {
      var q = new URLSearchParams(window.location.search);
      return {
        city: currentCity(),
        utm_source: q.get('utm_source') || '',
        utm_medium: q.get('utm_medium') || '',
        utm_campaign: q.get('utm_campaign') || '',
        landing_page: window.location.pathname.replace(/^\//, '') || 'index.html'
      };
    } catch (e) {
      return { city: currentCity(), utm_source: '', utm_medium: '', utm_campaign: '', landing_page: '' };
    }
  }

  /** 只保留白名单业务维度 */
  function pickProps(params) {
    var out = {};
    if (!params || typeof params !== 'object') return out;
    for (var k in params) {
      if (!Object.prototype.hasOwnProperty.call(params, k)) continue;
      if (!PROP_ALLOWED[k]) continue;
      var v = params[k];
      if (v === undefined || v === null) continue;
      if (typeof v === 'object') continue;
      var s = String(v);
      if (!s) continue;
      out[k] = s.slice(0, 80);
    }
    return out;
  }

  // ---------- 自建分析上报（完全静默失败） ----------
  var uaCache = null;
  function userAgent() {
    if (uaCache !== null) return uaCache;
    uaCache = '';
    try { uaCache = String(window.navigator.userAgent || '').slice(0, 200); }
    catch (e) { uaCache = ''; }
    return uaCache;
  }

  function buildPayload(eventName, params) {
    return {
      event: eventName,
      path: window.location.pathname + window.location.search,
      city: currentCity(),
      referrer: (document.referrer || '').slice(0, 300),
      session_id: sessionId(),
      ua: userAgent(),
      props: pickProps(params)
    };
  }

  function postSelf(payload) {
    var body;
    try { body = JSON.stringify(payload); }
    catch (e) { return; }
    if (!body) return;

    // 1) sendBeacon 优先（页面卸载也能发出去）
    try {
      if (window.navigator && typeof window.navigator.sendBeacon === 'function') {
        var blob = new Blob([body], { type: 'text/plain;charset=UTF-8' });
        if (window.navigator.sendBeacon(ANALYTICS_API, blob)) return;
      }
    } catch (e) { /* 回退到 fetch */ }

    // 2) fetch 回退（keepalive 保证离开页面时仍能发出）
    try {
      if (typeof window.fetch === 'function') {
        window.fetch(ANALYTICS_API, {
          method: 'POST',
          body: body,
          keepalive: true,
          mode: 'cors',
          headers: { 'Content-Type': 'text/plain;charset=UTF-8' }
        }).catch(function () { /* 静默 */ });
      }
    } catch (e) { /* 静默 */ }
  }

  /** 统一派发入口：任何时候调用都安全 */
  window.cwgTrack = function (eventName, params) {
    if (!eventName) return;
    try {
      if (GA_ENABLED) {
        window.gtag('event', eventName, params || {});
      }
    } catch (e) { /* 埋点失败绝不影响业务 */ }
    try {
      postSelf(buildPayload(eventName, params));
    } catch (e) { /* 埋点失败绝不影响业务 */ }
  };

  /** 自动 page_view：GA4 由 config 自动上报（不重复发），自建通道单独发一条 */
  function trackPageView() {
    try {
      postSelf(buildPayload('page_view', sessionContext()));
    } catch (e) { /* 静默 */ }
  }

  document.addEventListener('DOMContentLoaded', function () {

    // ---------- 0. page_view（自建通道补 GA4 自动上报） ----------
    trackPageView();

    // ---------- 1. WhatsApp / 电话 ----------
    document.addEventListener('click', function (e) {
      var el = e.target.closest ? e.target.closest('a,button') : null;
      if (!el) { return; }
      var href = el.getAttribute('href') || '';
      var cls = el.className || '';

      if (/wa\.me|whatsapp/i.test(href) || /whatsapp/i.test(cls)) {
        window.cwgTrack('whatsapp_click', Object.assign(sessionContext(), {
          label: (el.getAttribute('data-label') || el.textContent || '').trim().slice(0, 60)
        }));
      } else if (/^tel:/i.test(href)) {
        window.cwgTrack('phone_click', sessionContext());
      } else if (/city-card/i.test(cls)) {
        window.cwgTrack('city_card_click', Object.assign(sessionContext(), {
          city: (el.getAttribute('data-city') || currentCity())
        }));
      } else if (/price-cta|qb-cta|pl-cta/i.test(cls)) {
        window.cwgTrack('price_cta_click', sessionContext());
      }
    }, true);

    // ---------- 2. 导航点击 ----------
    var nav = document.querySelector('.nav-links');
    if (nav) {
      nav.addEventListener('click', function (e) {
        var a = e.target.closest ? e.target.closest('a') : null;
        if (!a) { return; }
        window.cwgTrack('nav_click', Object.assign(sessionContext(), {
          label: (a.textContent || '').trim().slice(0, 40)
        }));
      });
    }

    // ---------- 3. 表单开始（首次 focus = 有意图） ----------
    var started = {};
    document.addEventListener('focusin', function (e) {
      var f = e.target;
      if (!f || !f.form) { return; }
      var key = f.form.id || f.form.getAttribute('name') || 'form';
      if (started[key]) { return; }
      started[key] = true;
      var map = { bookingForm: 'booking_start', contactForm: 'contact_start' };
      if (map[key]) {
        window.cwgTrack(map[key], Object.assign(sessionContext(), {
          form_id: key
        }));
      }
    }, true);

    // ---------- 4. 表单提交（成功/失败都记） ----------
    document.addEventListener('submit', function (e) {
      var form = e.target;
      if (!form || !form.id) { return; }
      var map = { bookingForm: 'booking_submit', contactForm: 'contact_submit' };
      var ev = map[form.id];
      if (!ev) { return; }

      // 收集业务维度（不采集 PII，也不采集自由文本地点）
      var params = Object.assign(sessionContext(), { form_id: form.id });
      try {
        var fd = new FormData(form);
        var pick = function (keys) {
          for (var i = 0; i < keys.length; i++) {
            var v = fd.get(keys[i]);
            if (v) { return String(v).slice(0, 60); }
          }
          return '';
        };
        params.service_type = pick(['serviceType', 'service', 'service_type', 'tripType']);
        params.vehicle_type = pick(['vehicleType', 'vehicle', 'vehicle_type', 'carType']);
        params.city = params.city || pick(['city', 'destination', 'cityTo']);
      } catch (err) { /* ignore */ }

      window.cwgTrack(ev, params);

      // 若 3 秒内表单仍在 DOM 且没有跳转 → 判定失败
      window.setTimeout(function () {
        if (document.body.contains(form) && !form.dataset.cwgSubmitted) {
          // 错误事件名与口径表一致：booking → booking_error，contact → contact_submit_error
          var errEvent = (ev === 'booking_submit') ? 'booking_error' : 'contact_submit_error';
          window.cwgTrack(errEvent, Object.assign(sessionContext(), {
            form_id: form.id, reason: 'no_redirect'
          }));
        }
      }, 3000);
    }, true);

    // ---------- 5. 报价请求（前端报价 API） ----------
    var origFetch = window.fetch;
    if (origFetch) {
      window.fetch = function (input, init) {
        var url = (typeof input === 'string') ? input : (input && input.url) || '';
        var p = origFetch.apply(this, arguments);
        if (/\/api\/(quote|booking|contact)/.test(url)) {
          p.then(function (res) {
            window.cwgTrack('api_call', Object.assign(sessionContext(), {
              endpoint: url.replace(/^https?:\/\/[^/]+/, ''),
              status: res.status
            }));
          }).catch(function () { });
        }
        return p;
      };
    }
  });
})();

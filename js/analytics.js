/**
 * Chinawheely — GA4 埋点模块（集中式）
 *
 * 使用方式：
 *   1) 把下方 GA_MEASUREMENT_ID 改成你的 ID（形如 G-XXXXXXXXXX）
 *   2) 本文件已在所有页面通过 <script src="scripts.js"> 之前/之后加载即可
 *
 * 事件设计（对齐业务漏斗）：
 *   - page_view            自动（GA4 gtag 默认）
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
 * 全部通过 window.gtag 派发；未配置 ID 时静默降级，不影响页面。
 */
(function () {
  'use strict';

  // ★↓↓ 只需要改这一行 ★↓↓
  var GA_MEASUREMENT_ID = '';   // 例如 'G-ABC123XYZ'

  window.CWG_GA_ID = GA_MEASUREMENT_ID;
  var ENABLED = /^G-[A-Z0-9]{6,}$/i.test(GA_MEASUREMENT_ID);

  // ---------- 加载 gtag.js ----------
  if (ENABLED) {
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

  /** 统一派发入口：任何时候调用都安全 */
  window.cwgTrack = function (eventName, params) {
    if (!ENABLED) { return; }
    try {
      window.gtag('event', eventName, params || {});
    } catch (e) { /* 埋点失败绝不影响业务 */ }
  };

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

  if (!ENABLED) { return; }

  document.addEventListener('DOMContentLoaded', function () {

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
        var a = e.target.closest('a');
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

      // 收集关键字段（不采集 PII）
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
        params.pickup = pick(['pickup', 'from', 'pickupPoint', 'arrival']);
      } catch (err) { /* ignore */ }

      window.cwgTrack(ev, params);

      // 若 3 秒内表单仍在 DOM 且没有跳转 → 判定失败
      window.setTimeout(function () {
        if (document.body.contains(form) && !form.dataset.cwgSubmitted) {
          window.cwgTrack(ev + '_error', Object.assign(sessionContext(), {
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

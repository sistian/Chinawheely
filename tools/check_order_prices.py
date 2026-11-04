#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下单价格端到端验证（Chrome headless）：
  银川/台州新显式价 + 填充车型同价 + 控制城市 + intercity 同价 + 超时计费
用法: python3 tools/check_order_prices.py （需先开 http.server 8899）
"""
import json
import os
import subprocess
import sys

BASE = "/Users/w/Desktop/Chinawheely 10.27"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MARK = "CWPROBE::"

PROBE = r"""
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var out = { errors: [], cities: {} };
    window.onerror = function (m, s, l) { out.errors.push(String(m) + ' @' + l); };
    function q(sel) { return document.querySelector(sel); }
    function qa(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }

    // 读取 pricing.json 的期望值
    var expect = window.__EXPECT__;

    function pickCity(slug) {
      var sel = q('#city');
      for (var i = 0; i < sel.options.length; i++) {
        if (sel.options[i].value === slug) { sel.value = slug; break; }
      }
      sel.dispatchEvent(new Event('change', { bubbles: true }));
    }
    function pickVehicle(n) {
      var cards = qa('#vehicleRow input[name="vehicleChoice"]');
      if (cards[n]) { cards[n].checked = true; cards[n].dispatchEvent(new Event('change', { bubbles: true })); }
    }
    function pickTier(n) {
      var tiers = qa('#charterTiers input[name="tierChoice"]');
      if (tiers[n]) { tiers[n].checked = true; tiers[n].dispatchEvent(new Event('change', { bubbles: true })); }
    }
    function total() {
      var t = q('#quoteTotalCny');
      return t ? t.textContent.trim() : null;
    }
    function setProduct(p) {
      var el = q('input[name="product"][value="' + p + '"]');
      if (el) { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); }
    }

    ['yinchuan', 'taizhou', 'beijing', 'jiaxing'].forEach(function (slug) {
      pickCity(slug);
      var info = { label: null, airportCards: [], charterCoach2h: null, intercityEconomy: null, overtime: null };

      // 城市下拉标签
      var sel = q('#city');
      for (var i = 0; i < sel.options.length; i++) {
        if (sel.options[i].value === slug) info.label = sel.options[i].textContent.trim().slice(0, 40);
      }
      // 接送机 6 卡价格
      setProduct('airport');
      info.airportCards = qa('#vehicleRow .vehicle-price').map(function (e) { return e.textContent.trim(); });
      // intercity 与 economy 卡同价
      setProduct('intercity');
      info.intercityEconomy = q('#vehicleRow .vehicle-price') ? q('#vehicleRow .vehicle-price').textContent.trim() : null;
      // 包车 coach_19_55 第5卡 2h 档（切 charter → 选第5车型 → 第1档）
      setProduct('charter');
      pickVehicle(4); // coach_19_55 是第 5 张卡
      pickTier(0);    // 2h_35km
      info.charterCoach2h = total();
      // 超时 30 分钟
      var em = q('#extraMinutes');
      if (em) { em.value = '30'; em.dispatchEvent(new Event('change', { bubbles: true })); }
      info.overtime = total();
      if (em) { em.value = '0'; em.dispatchEvent(new Event('change', { bubbles: true })); }

      out.cities[slug] = info;
    });

    // 与期望值对拍
    out.mismatches = [];
    var exp = window.__EXPECT__;
    Object.keys(exp).forEach(function (slug) {
      var got = out.cities[slug] || {};
      var e = exp[slug];
      if (e.airportEconomy && got.airportCards[0] !== e.airportEconomy) {
        out.mismatches.push(slug + ' 接送机经济型: ' + got.airportCards[0] + ' ≠ 期望 ' + e.airportEconomy);
      }
      if (e.airportCoach && got.airportCards[5] !== e.airportCoach) {
        out.mismatches.push(slug + ' 接送机19-55座: ' + got.airportCards[5] + ' ≠ 期望 ' + e.airportCoach);
      }
      if (e.coach2h && got.charterCoach2h !== e.coach2h) {
        out.mismatches.push(slug + ' 包车19-55座 2h: ' + got.charterCoach2h + ' ≠ 期望 ' + e.coach2h);
      }
      if (e.intercity && got.intercityEconomy !== e.intercity) {
        out.mismatches.push(slug + ' 城际经济型: ' + got.intercityEconomy + ' ≠ 期望 ' + e.intercity);
      }
    });

    document.title = 'CWPROBE::' + JSON.stringify(out);
  }, 2600);
});
</script>
"""

# 期望值直接取自 pricing.json（引擎与页面共用同一数据源，浏览器实测 UI 渲染结果）
import json as _json
d = _json.load(open(f"{BASE}/pricing/pricing.json", encoding="utf-8"))
expect = {}
for slug in ["yinchuan", "taizhou", "beijing", "jiaxing"]:
    c = d["cities"][slug]
    expect[slug] = {
        "airportEconomy": f"¥{c['airport']['sedan_economy']['pkg']}",
        "airportCoach": f"¥{c['airport']['coach_19_55']['pkg']}",
        "coach2h": f"¥{c['charter']['coach_19_55']['tiers']['2h_35km']['pkg']}",
        "intercity": f"¥{c['airport']['sedan_economy']['pkg']}",  # intercity=airport
    }
expect_block = "<script>window.__EXPECT__=" + _json.dumps(expect) + ";</script>"

src = open(f"{BASE}/booking.html", encoding="utf-8").read()
probe_file = f"{BASE}/_probe_order_prices.html"
open(probe_file, "w", encoding="utf-8").write(
    src.replace("</head>", expect_block + "\n</head>").replace("</body>", PROBE + "\n</body>"))

try:
    r = subprocess.run([
        CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--virtual-time-budget=14000",
        "--dump-dom", "http://localhost:8899/_probe_order_prices.html"
    ], capture_output=True, text=True, timeout=150)
finally:
    os.unlink(probe_file)

dom = r.stdout
i = dom.find(MARK)
if i < 0:
    print("未拿到结果; stderr:", r.stderr[-400:])
    sys.exit(1)
j = dom.find("</title>", i)
raw = dom[i + len(MARK):j].replace("&quot;", '"').replace("&amp;", "&").replace("&#39;", "'")
data = _json.loads(raw)

print("== 期望值（来自 pricing.json）==")
for slug, e in expect.items():
    print(f"  {slug:9s} 经济型接送 {e['airportEconomy']:>6s} | 19-55座接送 {e['airportCoach']:>6s} | 包车19-55 2h {e['coach2h']:>6s}")

print("\n== 浏览器实测（booking 表单）==")
for slug, info in data.get("cities", {}).items():
    print(f"  {slug:9s} 下拉标签: {info.get('label')}")
    print(f"            接送机卡片: {info.get('airportCards')}")
    print(f"            城际经济型: {info.get('intercityEconomy')} | 包车19-55座2h: {info.get('charterCoach2h')} | +超时30分: {info.get('overtime')}")

mm = data.get("mismatches", [])
print(f"\n== 对拍结果: {len(mm)} 处不符 ==")
for m in mm:
    print("  ✗", m)
if data.get("errors"):
    print("JS 错误:", data["errors"])
print("✓ 全部一致" if not mm and not data.get("errors") else "✗ 存在不符")
sys.exit(0 if not mm and not data.get("errors") else 1)

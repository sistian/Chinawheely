#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用 Chrome headless 真实渲染 booking.html，检查表单加载与报价是否正常。
做法：把探针脚本注入 booking.html 副本（同源，fetch 可用），dump-dom 读 title。
用法: python3 tools/check_form.py [url]
"""
import json
import os
import re
import subprocess
import sys

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8899/booking.html"
BASE = "/Users/w/Desktop/Chinawheely 10.27"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MARK = "CWPROBE::"

PROBE = r"""
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var out = { errors: [], steps: {} };
    window.onerror = function (m, s, l) { out.errors.push(String(m) + ' @' + l); };
    function q(sel) { return document.querySelector(sel); }
    function qa(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }

    out.steps.corePresent = !!(window.CWPricing && window.CWPricing.quote);
    out.steps.airportDbCount = (window.AIRPORT_DB && Object.keys(window.AIRPORT_DB).length) || 0;
    out.steps.cityOptions = q('#city') ? q('#city').options.length : 0;
    out.steps.cityFirstFew = q('#city') ? Array.prototype.slice.call(q('#city').options).slice(0, 4)
        .map(function (o) { return o.value + '=' + o.textContent.slice(0, 30); }) : [];

    var citySel = q('#city');
    if (citySel) {
      for (var i = 0; i < citySel.options.length; i++) {
        if (citySel.options[i].value === 'beijing') {
          citySel.value = 'beijing';
          citySel.dispatchEvent(new Event('change', { bubbles: true }));
          break;
        }
      }
    }
    out.steps.vehicleCards = qa('#vehicleRow .vehicle-option').length;
    out.steps.vehiclePrices = qa('#vehicleRow .vehicle-price').map(function (e) { return e.textContent.trim(); });
    out.steps.airportOptions = q('#airport') ? q('#airport').options.length : 0;
    out.steps.airportFirst = q('#airport') ? Array.prototype.slice.call(q('#airport').options)
        .map(function (o) { return o.textContent.slice(0, 42); }) : [];
    out.steps.quoteTotalCny = q('#quoteTotalCny') ? q('#quoteTotalCny').textContent : null;
    out.steps.quoteTotalUsd = q('#quoteTotalUsd') ? q('#quoteTotalUsd').textContent : null;
    out.steps.quoteRows = qa('#quoteRows .quote-row').map(function (e) { return e.textContent.trim(); });

    var veh = q('#vehicleRow input[name="vehicleChoice"]');
    if (veh) { veh.checked = true; veh.dispatchEvent(new Event('change', { bubbles: true })); }
    out.steps.quoteAfterVehicle = q('#quoteTotalCny') ? q('#quoteTotalCny').textContent : null;

    var em = q('#extraMinutes');
    if (em) { em.value = '30'; em.dispatchEvent(new Event('change', { bubbles: true })); }
    out.steps.quoteAfterOvertime = q('#quoteTotalCny') ? q('#quoteTotalCny').textContent : null;
    out.steps.quoteRowsAfter = qa('#quoteRows .quote-row').map(function (e) { return e.textContent.trim(); });

    var charter = q('input[name="product"][value="charter"]');
    if (charter) {
      charter.checked = true;
      charter.dispatchEvent(new Event('change', { bubbles: true }));
    }
    out.steps.charterTierCards = qa('#charterTiers input[name="tierChoice"]').length;
    out.steps.charterVehicleCards = qa('#vehicleRow .vehicle-option').length;
    out.steps.charterTierLabels = qa('#charterTiers .service-option-note').map(function (e) { return e.textContent.trim(); });
    out.steps.quoteCharter = q('#quoteTotalCny') ? q('#quoteTotalCny').textContent : null;

    var interc = q('input[name="product"][value="intercity"]');
    if (interc) {
      interc.checked = true;
      interc.dispatchEvent(new Event('change', { bubbles: true }));
    }
    out.steps.quoteIntercity = q('#quoteTotalCny') ? q('#quoteTotalCny').textContent : null;
    out.steps.intercityVisible = q('#intercityFields') ? q('#intercityFields').style.display : null;

    out.steps.hidden = {
      product: q('#formProduct') ? q('#formProduct').value : null,
      vehicle: q('#formVehicleKey') ? q('#formVehicleKey').value : null,
      tier: q('#formTierKey') ? q('#formTierKey').value : null,
      extraMinutes: q('#formExtraMinutes') ? q('#formExtraMinutes').value : null,
      totalCny: q('#formTotalCny') ? q('#formTotalCny').value : null,
      totalUsd: q('#formTotalUsd') ? q('#formTotalUsd').value : null,
      breakdown: q('#formBreakdown') ? q('#formBreakdown').value.slice(0, 150) : null
    };
    document.title = 'CWPROBE::' + JSON.stringify(out);
  }, 2200);
});
</script>
"""

src = open(f"{BASE}/booking.html", encoding="utf-8").read()
probe_file = f"{BASE}/_probe_booking.html"
open(probe_file, "w", encoding="utf-8").write(src.replace("</body>", PROBE + "\n</body>"))

try:
    out = subprocess.run([
        CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--virtual-time-budget=12000",
        "--dump-dom", f"http://localhost:8899/_probe_booking.html"
    ], capture_output=True, text=True, timeout=120)
finally:
    os.unlink(probe_file)

dom = out.stdout
idx = dom.find(MARK)
if idx < 0:
    print("未拿到探针结果。stderr 尾部:", out.stderr[-800:])
    sys.exit(1)
end = dom.find("</title>", idx)
raw = dom[idx + len(MARK):end]
raw = (raw.replace("&quot;", '"').replace("&#39;", "'")
          .replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
try:
    data = json.loads(raw)
except Exception as e:
    print("解析失败:", e)
    print(raw[:3000])
    sys.exit(1)

print(json.dumps(data, ensure_ascii=False, indent=2))

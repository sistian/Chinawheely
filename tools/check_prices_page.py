#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chrome headless 检查 prices.html 渲染 + 替换后城市页无残留假价格"""
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
    var out = {};
    function q(s){return document.querySelector(s);}
    function qa(s){return Array.prototype.slice.call(document.querySelectorAll(s));}
    out.title = document.title;
    out.cityCards = qa('.city').length;
    out.openDefault = qa('details[open]').length;
    var bj = qa('.city').filter(function(c){return c.getAttribute('data-slug')==='beijing';})[0];
    if (bj) {
      bj.setAttribute('open','');
      out.beijingFrom = bj.querySelector('.city-from').textContent.trim();
      out.bjRows = bj.querySelectorAll('tbody tr').length;
      out.bjFirstPrice = bj.querySelector('td.price').textContent;
      out.bjFirstUsd = bj.querySelector('td.usd').textContent;
    }
    // 搜索功能
    var qEl = document.getElementById('q');
    if (qEl) {
      qEl.value = 'sanya';
      qEl.dispatchEvent(new Event('input'));
      out.searchVisible = qa('.city').filter(function(c){return c.style.display !== 'none';}).length;
      qEl.value = '';
      qEl.dispatchEvent(new Event('input'));
    }
    // 链接
    out.ctaLinks = qa('.book-cta').length;
    var badLinks = qa('a[href="booking.html"]').length;
    out.bookingLinks = badLinks;
    document.title = 'CWPROBE::' + JSON.stringify(out);
  }, 1500);
});
</script>
"""

src = open(f"{BASE}/prices.html", encoding="utf-8").read()
probe_file = f"{BASE}/_probe_prices.html"
open(probe_file, "w", encoding="utf-8").write(src.replace("</body>", PROBE + "\n</body>"))

try:
    r = subprocess.run([
        CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--virtual-time-budget=10000",
        "--dump-dom", "http://localhost:8899/_probe_prices.html"
    ], capture_output=True, text=True, timeout=120)
finally:
    os.unlink(probe_file)

dom = r.stdout
i = dom.find(MARK)
if i < 0:
    print("未拿到结果", r.stderr[-500:])
    sys.exit(1)
j = dom.find("</title>", i)
raw = dom[i + len(MARK):j].replace("&quot;", '"').replace("&amp;", "&")
print(json.dumps(json.loads(raw), ensure_ascii=False, indent=2))

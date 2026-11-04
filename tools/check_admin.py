#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chrome headless 检查 admin.html：JS 无错 + 两个 Tab 存在 + 关键元素齐全"""
import json
import os
import re
import subprocess
import sys

BASE = "/Users/w/Desktop/Chinawheely 10.27"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MARK = "CWPROBE::"

PROBE = r"""
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var out = { errors: [] };
    window.onerror = function (m, s, l) { out.errors.push(String(m) + ' @' + l); };
    function $(id){ return document.getElementById(id); }
    function qa(s){ return Array.prototype.slice.call(document.querySelectorAll(s)); }
    out.loginVisible = !$('loginView').classList.contains('hidden');
    out.tabCount = qa('.tab-btn').length;
    out.tabLabels = qa('.tab-btn').map(function(b){ return b.textContent.trim().slice(0,6); });
    out.viewLeadsExists = !!$('viewLeads');
    out.viewOrdersExists = !!$('viewOrders');
    out.ordersHidden = $('viewOrders') ? $('viewOrders').classList.contains('hidden') : null;
    out.oStatsExists = !!$('oStats');
    out.oRowsExists = !!$('oRows');
    out.oDrawerExists = !!$('oDrawer');
    out.oFilterCount = ['oFStatus','oFPay','oFFrom','oFTo','oFQ'].filter(function(id){ return !!$(id); }).length;
    out.manageOrderLink = !!document.querySelector('link[rel="canonical"]');
    // leads 表头还在
    out.leadsTableHeaders = qa('#viewLeads thead th').length;
    out.ordersTableHeaders = qa('#viewOrders thead th').length;
    document.title = 'CWPROBE::' + JSON.stringify(out);
  }, 1200);
});
</script>
"""

for page in ["admin.html", "manage-order.html"]:
    src = open(f"{BASE}/{page}", encoding="utf-8").read()
    probe_file = f"{BASE}/_probe_admin.html"
    open(probe_file, "w", encoding="utf-8").write(src.replace("</body>", PROBE + "\n</body>"))
    try:
        r = subprocess.run([
            CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
            "--virtual-time-budget=8000",
            "--dump-dom", f"http://localhost:8899/_probe_admin.html"
        ], capture_output=True, text=True, timeout=90)
    finally:
        os.unlink(probe_file)
    dom = r.stdout
    i = dom.find(MARK)
    if i < 0:
        print(f"[{page}] 未拿到结果; stderr:", r.stderr[-300:])
        continue
    j = dom.find("</title>", i)
    raw = dom[i + len(MARK):j].replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")
    print(f"===== {page} =====")
    try:
        print(json.dumps(json.loads(raw), ensure_ascii=False, indent=1))
    except Exception as e:
        print("RAW:", raw[:800])

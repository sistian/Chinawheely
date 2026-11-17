#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证首页城市卡片区的交互：字母筛选 / Browse All 展开收起。

用 headless Chrome 加载真实 index.html，注入 JS 模拟点击，
读出各状态下可见卡片数，确认逻辑正确。
"""
import json
import os
import re
import subprocess
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PROBE_JS = r"""
(function(){
  var out = {};
  var cards = document.querySelectorAll('.city-card-wrapper');
  out.total = cards.length;
  function visible(){
    var n=0;
    cards.forEach(function(c){ if(!c.classList.contains('hidden')) n++; });
    return n;
  }
  function call(fn, btn, arg){
    try { fn(btn, arg); } catch(e) { out.err = String(e); }
  }
  // 展开前
  out.initiallyVisible = visible();

  // 字母筛选 B
  var btnB = document.querySelector('.letter-btn[onclick*="\'B\'"]');
  if (btnB) { call(window.filterByLetter3, btnB, 'B'); out.afterB = visible(); }
  else out.afterB = null;

  // 回到 ALL
  var btnAll = document.querySelector('.letter-btn[onclick*="\'ALL\'"]');
  if (btnAll) { call(window.filterByLetter3, btnAll, 'ALL'); out.afterAll = visible(); }
  else out.afterAll = null;

  // Browse All 展开
  var bb = document.getElementById('browseAllBtn');
  if (bb) {
    call(window.toggleBrowseAll, bb);
    out.afterBrowseClick = visible();
    out.browseLabel = bb.textContent.replace(/\s+/g,' ').trim();
    call(window.toggleBrowseAll, bb);
    out.afterBrowseUnclick = visible();
  }
  var d = document.createElement('div');
  d.id = '__PROBE_OUT__';
  d.textContent = JSON.stringify(out);
  document.body.appendChild(d);
})()
"""


def main():
    url = "file://" + os.path.join(SITE, "index.html").replace(" ", "%20")
    dump = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--force-prefers-reduced-motion",
         "--virtual-time-budget=12000", "--dump-dom", url],
        capture_output=True, timeout=180).stdout.decode("utf-8", "replace")
    # 用 --dump-dom 拿不到 JS 返回值，改用注入式：写临时 html 带 script 输出
    tmp = os.path.join(SITE, "_probe_interact.html")
    html = dump.replace("</body>", "<script>" + PROBE_JS + "</script></body>")
    open(tmp, "w", encoding="utf-8").write(html)
    try:
        out = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--force-prefers-reduced-motion",
             "--virtual-time-budget=12000", "--dump-dom",
             "file://" + tmp.replace(" ", "%20")],
            capture_output=True, timeout=180).stdout.decode("utf-8", "replace")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    m = re.search(r'<div id="__PROBE_OUT__">(.*?)</div>', out, re.S)
    if not m:
        print("未取到探针结果")
        print(out[-1500:])
        return 1
    import html as _html
    print(json.dumps(json.loads(_html.unescape(m.group(1))), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

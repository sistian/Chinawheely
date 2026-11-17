#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「城市卡片区」的独立截图，用于精确核对视觉。

把 index.html 的 <head> + #cities 板块单独抽成一个临时页面，
这样布局确定、截图可控（不受 hero 的 100vh 影响）。

用法： python3 tools/cw_shot_cities.py [输出png]
"""
import os
import re
import subprocess
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cw_shots/cities_only.png"
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    head = h[: h.find("</head>") + len("</head>")]
    i = h.find('<section class="section section-dark" id="cities">')
    j = h.find("</section>", i) + len("</section>")
    sec = h[i:j]
    tmp = os.path.join(SITE, "_shot_cities.html")
    page = head + '<body style="padding-top:0">' + sec + '</body></html>'
    open(tmp, "w", encoding="utf-8").write(page)
    try:
        url = "file://" + tmp.replace(" ", "%20")
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--force-prefers-reduced-motion",
             "--hide-scrollbars", "--virtual-time-budget=20000",
             "--window-size=1440,2600", "--screenshot=" + out, url],
            capture_output=True, timeout=180)
        print("截图:", out, os.path.getsize(out) if os.path.exists(out) else "FAILED")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())

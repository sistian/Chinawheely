#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""渲染单张城市卡片的放大图，用于精确核对「中文名 + 英文名」的视觉效果。

用法： python3 tools/cw_shot_one_card.py [slug] [输出png]
"""
import os
import re
import subprocess
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else "beijing"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/cw_shots/one_card.png"
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    head = h[: h.find("</head>") + len("</head>")]

    blocks = re.findall(r'<div class="city-card-wrapper">.*?</div>\s*</div>', h, re.S)
    card = None
    for b in blocks:
        if f'href="{slug}.html"' in b:
            card = b
            break
    if not card:
        print("未找到卡片:", slug)
        return 1

    page = (head + '<body style="background:#0d3d27;padding:40px">'
            '<div style="width:900px">' + card + '</div>'
            '<div style="width:420px;margin-top:20px">' + card + '</div>'
            '</body></html>')
    tmp = os.path.join(SITE, "_shot_card.html")
    open(tmp, "w", encoding="utf-8").write(page)
    try:
        url = "file://" + tmp.replace(" ", "%20")
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--force-prefers-reduced-motion",
             "--hide-scrollbars", "--virtual-time-budget=15000",
             "--window-size=1000,800", "--screenshot=" + out, url],
            capture_output=True, timeout=180)
        print("截图:", out, os.path.getsize(out) if os.path.exists(out) else "FAILED")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())

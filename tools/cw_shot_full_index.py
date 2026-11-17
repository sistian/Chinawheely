#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对真实 index.html 做整页截图（headless Chrome），用于端到端视觉核对。

用法： python3 tools/cw_shot_full_index.py [输出png] [窗口宽] [窗口高]
"""
import os
import subprocess
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cw_shots/index_full.png"
    w = sys.argv[2] if len(sys.argv) > 2 else "1440"
    hgt = sys.argv[3] if len(sys.argv) > 3 else "2600"
    url = "file://" + os.path.join(SITE, "index.html").replace(" ", "%20")
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--force-prefers-reduced-motion",
         "--hide-scrollbars", "--virtual-time-budget=20000",
         "--window-size=%s,%s" % (w, hgt), "--screenshot=" + out, url],
        capture_output=True, timeout=240)
    print("截图:", out, os.path.getsize(out) if os.path.exists(out) else "FAILED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

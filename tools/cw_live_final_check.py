#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上终验：首页城市板块截图 + yuzhou 卡中文名确认。"""
import subprocess
import time

OUT = "/tmp/cw_shots/live_final2.png"


def main():
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    url = "https://www.chinawheely.com/?v=final2"
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", "--force-prefers-reduced-motion",
                    "--window-size=1440,2400",
                    "--screenshot=" + OUT, url], check=False, timeout=120)
    time.sleep(1)
    # 用 dump-dom 验证 yuzhou 卡
    r = subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                        "--dump-dom", url + "&dom=1"], capture_output=True,
                       text=True, timeout=120)
    dom = r.stdout
    i = dom.find('href="yuzhou.html"')
    print("yuzhou 卡片段:", dom[i:i + 320].replace("\n", " ")[:300] if i >= 0 else "未找到")
    for s in ["bitu", "qiqihar", "karakax", "yuxian"]:
        print("网格内 %s: %s" % (s, ('href="%s.html"' % s) in dom))
    print("city-card-wrapper 数:", dom.count("city-card-wrapper"))
    print("截图:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

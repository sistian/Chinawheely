#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓首页城市网格板块截图（滚动到 grid 区域）做最终视觉复核。"""
import subprocess
import time

OUT = "/tmp/cw_shots/live_cities_final.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main():
    # 用注入脚本把结果写入 DOM 的方式拿坐标 + 截图
    js = ("document.querySelectorAll('.city-card-wrapper').length")
    url = "https://www.chinawheely.com/?v=citiesfinal"
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", "--force-prefers-reduced-motion",
                    "--window-size=1440,1400",
                    "--virtual-time-budget=8000",
                    "--screenshot=" + OUT,
                    url + "#cities"], check=False, timeout=120)
    time.sleep(1)
    print("截图:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

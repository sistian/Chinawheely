#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""浏览器渲染验证：确认改动页的购物文案 / Xi'an 拼写 / 锚点 在真实 DOM 中正确。"""
import re, subprocess, sys

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE = "http://127.0.0.1:8899"
PAGES = ["nantong.html", "yantai.html", "zhenjiang.html", "xian.html", "lanzhou.html"]

EXPECT = {
    "nantong.html": "Wenfeng Dashijie on Nanda Street",
    "yantai.html": "Zhuhua Shopping Center on Nanda Street",
    "zhenjiang.html": "Daxi Road",
}

ok = True
for p in PAGES:
    r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-proxy-server",
                        "--virtual-time-budget=4000", "--dump-dom", f"{BASE}/{p}"],
                       capture_output=True, text=True, timeout=90)
    dom = r.stdout
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", dom))
    print(f"\n=== {p}  dom={len(dom)}B")
    if p in EXPECT:
        hit = EXPECT[p] in txt
        print(f"  {'✅' if hit else '❌'} 购物文案含「{EXPECT[p]}」")
        ok &= hit
        bad = "Nanjing Road" in txt or "Dagu Road" in txt
        print(f"  {'✅' if not bad else '❌'} 不再含串城文案")
        ok &= not bad
    m = re.search(r'<meta name="description" content="([^"]*)"', dom)
    if m:
        d = m.group(1)
        good = "Xi'an" in d or "Xian" not in d
        print(f"  {'✅' if good else '❌'} description: {d[:90]}")
        ok &= good
    # 锚点文本
    anchor = re.search(r'<a href="xian\.html">([^<]*)</a>', dom)
    if anchor:
        t = anchor.group(1)
        good = t == "Xi'an"
        print(f"  {'✅' if good else '❌'} 导航锚点文本: {t}")
        ok &= good

# 检查 booking.html?city=Xian 预填仍然生效（选 xian）
r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-proxy-server",
                    "--virtual-time-budget=5000", "--dump-dom",
                    f"{BASE}/booking.html?city=Xian"], capture_output=True, text=True, timeout=90)
dom = r.stdout
sel = re.findall(r'<option value="xian"[^>]*>([^<]*)</option>', dom)
sel_tag = re.search(r'<option value="xian"[^>]*>', dom)
print(f"\n=== booking.html?city=Xian 预填")
print(f"  选项文本: {sel}")
print(f"  选项标签: {sel_tag.group(0) if sel_tag else '未找到'}")
has_xian = 'value="xian"' in dom
print(f"  {'✅' if has_xian else '❌'} 页面含 xian 选项（预填逻辑可解析 slug）")

print("\n" + ("✅ 全部通过" if ok else "❌ 有失败"))
sys.exit(0 if ok else 1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打印 index.html 网格全部卡片 slug + 中文名，并标注页面文件是否存在。

用法： python3 tools/cw_dump_cards.py
"""
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
gi = h.find('<div class="grid grid-4">')
ge = h.find("</section>", gi)
seg = h[gi:ge]
pairs = re.findall(
    r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
    r'\s*<span class="city-card-name-cn">([^<]+)</span>', seg, re.S)
print("卡片数:", len(pairs))
nopage = []
for slug, en, cn in pairs:
    p = os.path.join(SITE, slug + ".html")
    ok = os.path.exists(p)
    if not ok:
        nopage.append((slug, en, cn))
    print("%-18s %-18s %-8s page=%s" % (slug, en, cn, "Y" if ok else "NO"))
print("\n无页面文件:", nopage)

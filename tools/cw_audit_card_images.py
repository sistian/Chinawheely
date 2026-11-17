#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对首页每张卡片的图片文件名是否与自己的 slug 一致。

同时统计：同图被多张卡复用的情况。
"""
import os
import re
from collections import defaultdict

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    seg = h[gi:ge]
    parts = re.split(r'(?=<div class="city-card-wrapper">)', seg)
    cards = [p for p in parts if p.startswith('<div class="city-card-wrapper">')]

    rows = []
    for c in cards:
        slug = re.search(r'city-card" href="([a-z_0-9]+)\.html"', c).group(1)
        im = re.search(r'src="(images/card/[^"]+)"', c)
        sty = re.search(r"background-image:url\('([^']+)'\)", c)
        cn = re.search(r'city-card-name-cn">([^<]+)', c)
        en = re.search(r'city-card-name">([^<]+)', c)
        path = im.group(1) if im else (sty.group(1) if sty else "")
        rows.append((slug, en.group(1) if en else "", cn.group(1) if cn else "",
                     os.path.basename(path).replace(".webp", "") if path else ""))

    print("卡片总数:", len(rows))

    print("\n=== 1) 图片文件名与 slug 不一致 ===")
    bad = 0
    for slug, en, cn, imgbase in rows:
        if imgbase and imgbase != slug:
            bad += 1
            print("  %-11s 卡中文=%-7s 图=%-16s <-- 不匹配" % (slug, cn, imgbase))
    print("  合计 %d 处" % bad)

    print("\n=== 2) 同一张图被多张卡复用 ===")
    d = defaultdict(list)
    for slug, en, cn, imgbase in rows:
        if imgbase:
            d[imgbase].append((slug, cn))
    n = 0
    for img, v in sorted(d.items()):
        if len(v) > 1:
            n += 1
            print("  %-16s <- %s" % (img, v))
    print("  合计 %d 组" % n)

    print("\n=== 3) 中文名重复 ===")
    d2 = defaultdict(list)
    for slug, en, cn, imgbase in rows:
        d2[cn].append(slug)
    for cn, v in sorted(d2.items()):
        if len(v) > 1:
            print("  %-8s <- %s" % (cn, v))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

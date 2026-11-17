#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给「images/ 里有实拍图、但页面还没有画廊段」的城市页补上 In Pictures 段。

插入位置：hero 段之后、第一个正文 section 之前（与已有城市页的顺序一致）。
同时在页面 TOC 里加一条目录项（若页面有 TOC 导航）。
"""
import json
import os
import re
import sys

SITE = "/Users/w/Desktop/Chinawheely 10.27"
imgs = os.path.join(SITE, "images")
pricing = json.load(open(os.path.join(SITE, "pricing", "pricing.json"), encoding="utf-8"))["cities"]

SKIP = {"index", "beijing_detailed", "bitu", "qiqihar", "karakax", "erdos", "wulumuqi"}


def city_en(slug):
    c = pricing.get(slug) or {}
    return c.get("en") or slug


def main():
    gal = {}
    for f in os.listdir(imgs):
        m = re.match(r"^(.+?)-g(\d+)\.webp$", f)
        if m:
            gal.setdefault(m.group(1), []).append(int(m.group(2)))

    made = []
    for fn in sorted(os.listdir(SITE)):
        if not fn.endswith(".html"):
            continue
        slug = fn[:-5]
        if slug in SKIP or slug not in gal:
            continue
        p = os.path.join(SITE, fn)
        h = open(p, encoding="utf-8").read()
        if "city-gallery-grid" in h:
            continue
        # 别名页（canonical 指向别处）不插
        cm = re.search(r'<link rel="canonical" href="([^"]+)"', h)
        if cm and cm.group(1).rstrip("/").split("/")[-1] not in (slug + ".html",):
            continue
        if 'rel="canonical"' not in h:
            continue

        nums = sorted(gal[slug])
        figs = "".join(
            '<figure class="city-gallery-item"><img src="images/%s-g%d.webp" alt="%s photo %d" '
            'loading="lazy" decoding="async" width="900" height="600"></figure>'
            % (slug, n, city_en(slug), n) for n in nums)
        en = city_en(slug)
        block = ('<section class="city-gallery"><div class="container"><div class="section-header">'
                 '<h2 id="toc-%s-in-pictures">%s in Pictures</h2><div class="divider"></div>'
                 '<p>Real scenes from %s — landmarks, streets and everyday life.</p></div>'
                 '<div class="city-gallery-grid">%s</div></div></section>'
                 % (slug, en, en, figs))

        # 插入点：hero section 结束处
        m = re.search(r'<section class="hero[^"]*"[^>]*>.*?</section>', h, re.S)
        if not m:
            print("  跳过（无 hero 段）:", slug)
            continue
        cut = m.end()
        h = h[:cut] + block + h[cut:]

        # TOC 加目录项
        toc = re.search(r'(<nav class="toc"[^>]*>.*?<ul>)', h, re.S)
        if toc:
            h = h[:toc.end()] + ('<li><a href="#toc-%s-in-pictures">%s in Pictures</a></li>'
                                 % (slug, en)) + h[toc.end():]
        open(p, "w", encoding="utf-8").write(h)
        made.append((slug, len(nums)))

    print("新增画廊段的城市页: %d" % len(made))
    for s, n in made:
        print("   %-18s %d 张" % (s, n))


if __name__ == "__main__":
    main()

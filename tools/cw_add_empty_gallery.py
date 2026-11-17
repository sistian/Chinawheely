#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给「源目录有照片、但页面还没有画廊段」的城市页先建一个空画廊段，
随后由 cw_expand_galleries.py 填入实拍图。

（例：齐齐哈尔有 7 张源图，但页面既没有画廊段、也没引用任何图。）
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cw_build_city_images as base

SITE = base.SITE
pricing = json.load(open(os.path.join(SITE, "pricing", "pricing.json"), encoding="utf-8"))["cities"]

SKIP = {"index", "beijing_detailed", "bitu", "qiqihar", "karakax", "erdos", "wulumuqi", "ulaanbaatar"}


def city_en(slug):
    c = pricing.get(slug) or {}
    return c.get("en") or slug


def main():
    cards, page_cn = base.load_site_maps()
    src_idx = base.build_source_index()
    mapping, _ = base.build_mapping(src_idx, cards, page_cn)

    made = []
    for slug in sorted(mapping):
        if slug in SKIP:
            continue
        p = os.path.join(SITE, slug + ".html")
        if not os.path.exists(p):
            continue
        h = open(p, encoding="utf-8").read()
        if "city-gallery-grid" in h:
            continue
        m = re.search(r'<section class="hero[^"]*"[^>]*>.*?</section>', h, re.S)
        if not m:
            continue
        en = city_en(slug)
        block = ('<section class="city-gallery"><div class="container"><div class="section-header">'
                 '<h2 id="toc-%s-in-pictures">%s in Pictures</h2><div class="divider"></div>'
                 '<p>Real scenes from %s — landmarks, streets and everyday life.</p></div>'
                 '<div class="city-gallery-grid"></div></div></section>' % (slug, en, en))
        h = h[:m.end()] + block + h[m.end():]
        toc = re.search(r'(<nav class="toc"[^>]*>.*?<ul>)', h, re.S)
        if toc:
            h = h[:toc.end()] + ('<li><a href="#toc-%s-in-pictures">%s in Pictures</a></li>'
                                 % (slug, en)) + h[toc.end():]
        open(p, "w", encoding="utf-8").write(h)
        made.append(slug)

    print("新建空画廊段: %d 个页面 -> %s" % (len(made), made))


if __name__ == "__main__":
    main()

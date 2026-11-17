#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""终验：
  1. index.html 网格卡数 / 唯一 CN / 唯一 slug / CTA 保留
  2. 4 个别名页 robots+canonical
  3. sitemap 条目数 + 无 karakax/yuxian/bitu/qiqihar
  4. cities.html / prices.html 城市数
  5. 全站无指向别名页的残留链接
"""
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    cards = re.findall(
        r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
        r'\s*<span class="city-card-name-cn">([^<]+)</span>', h[gi:ge], re.S)
    slugs = [s for s, _e, _c in cards]
    cns = [c.strip() for _s, _e, c in cards]
    print("1) 网格卡片: %d  唯一slug: %d  唯一CN: %d  CTA保留: %s" % (
        len(cards), len(set(slugs)), len(set(cns)), "See All Cities" in h[gi:ge + 2000] or "See All Cities" in h))

    print("\n2) 别名页元数据:")
    for s in ["bitu", "qiqihar", "karakax", "yuxian"]:
        t = open(os.path.join(SITE, s + ".html"), encoding="utf-8").read()
        r = re.search(r'robots" content="([^"]*)"', t)
        c = re.search(r'canonical" href="([^"]*)"', t)
        print("   %-9s robots=%s canon=%s" % (s, r.group(1) if r else "?", c.group(1) if c else "?"))

    sm = open(os.path.join(SITE, "sitemap.xml"), encoding="utf-8").read()
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    bad = [u for u in locs if any("/%s.html" % s in u for s in
                                  ["karakax", "yuxian", "bitu", "qiqihar"])]
    print("\n3) sitemap: %d 条  别名页残留: %s" % (len(locs), bad or "无"))

    ch = open(os.path.join(SITE, "cities.html"), encoding="utf-8").read()
    clinks = re.findall(r'href="([a-z_0-9]+)\.html"', ch)
    ccity = [s for s in clugs_test(clinks)] if False else None
    ph = open(os.path.join(SITE, "prices.html"), encoding="utf-8").read()
    pcities = re.findall(r'data-slug="([a-z_0-9]+)"', ph)
    print("\n4) cities.html 链接城市(去重): %d  prices.html 城市块: %d" % (
        len(set(clinks)), len(pcities)))

    n = 0
    for f in sorted(os.listdir(SITE)):
        if not f.endswith(".html") or f[:-5] in ("bitu", "qiqihar", "karakax", "yuxian"):
            continue
        t = open(os.path.join(SITE, f), encoding="utf-8", errors="replace").read()
        for s in ["bitu", "qiqihar", "karakax", "yuxian"]:
            n += len(re.findall(r'href="%s\.html"' % s, t))
    print("\n5) 全站指向别名页的残留链接: %d" % n)

    # 卡片区重复 CN 复查
    from collections import Counter
    dup = [c for c, k in Counter(cns).items() if k > 1]
    print("   网格重复CN: %s" % (dup or "无"))
    return 0


def clugs_test(x):
    return x


if __name__ == "__main__":
    raise SystemExit(main())

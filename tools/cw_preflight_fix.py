#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收集修复前的事实：cities.html / prices.html / sitemap / 全站锚文本中
问题 slug（bitu qiqihar karakax yuxian yuzhou）的写法与位置。
"""
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUGS = ["bitu", "qiqihar", "karakax", "yuxian", "yuzhou", "bozhou",
         "fuzhou_jx", "fuzhou", "suzhou_ah", "suzhou"]


def show(fname, label):
    p = os.path.join(SITE, fname)
    if not os.path.exists(p):
        print("%-14s 无此文件" % label)
        return
    h = open(p, encoding="utf-8", errors="replace").read()
    print("=== %s ===" % label)
    for s in SLUGS:
        pats = re.findall(r'.{0,60}href="%s\.html".{0,80}' % s, h)
        for x in pats[:2]:
            print("   %s: %s" % (s, re.sub(r"\s+", " ", x)))
        if not pats:
            # sitemap 用 <loc>
            loc = re.findall(r"<loc>[^<]*%s\.html</loc>" % s, h)
            if loc:
                print("   %s: [sitemap loc] %s" % (s, loc[0]))
    print()


def main():
    show("cities.html", "cities.html")
    show("prices.html", "prices.html")
    show("sitemap.xml", "sitemap.xml")

    # 全站锚文本：链接到问题 slug 但锚文本含错误中文名
    print("=== 全站 错误中文名 锚文本 ===")
    bad_pairs = [("yuzhou.html", "亳州"), ("karakax.html", "喀什"),
                 ("yuxian.html", "玉溪"), ("bozhou.html", "禹州"),
                 ("kashgar.html", "和田"), ("hoting.html", "喀什")]
    n = 0
    for f in sorted(os.listdir(SITE)):
        if not f.endswith(".html"):
            continue
        p = os.path.join(SITE, f)
        h = open(p, encoding="utf-8", errors="replace").read()
        for tgt, bad in bad_pairs:
            for m in re.finditer(r'<a[^>]*href="%s"[^>]*>([^<]*)</a>' % tgt, h):
                if bad in m.group(1):
                    n += 1
                    if n <= 30:
                        print("   %-22s -> %s  锚=%s" % (f, tgt, m.group(1).strip()[:40]))
    print("   合计 %d 处" % n)

    # yuzhou.html / yuxian.html / karakax.html 页内的错误中文名出现次数
    for slug, bad in [("yuzhou", "亳州"), ("yuxian", "玉溪"), ("karakax", "喀什")]:
        p = os.path.join(SITE, slug + ".html")
        h = open(p, encoding="utf-8", errors="replace").read()
        cnt = h.count(bad)
        where = []
        m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
        if m:
            where.append("h1=" + re.sub(r"<[^>]+>", "", m.group(1)).strip()[:40])
        m = re.search(r'<link rel="canonical" href="([^"]*)"', h)
        where.append("canon=" + (m.group(1) if m else "?"))
        m = re.search(r'<meta name="robots" content="([^"]*)"', h)
        where.append("robots=" + (m.group(1) if m else "?"))
        print("%s.html: 「%s」出现 %d 次 | %s" % (slug, bad, cnt, " | ".join(where)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复首页/城市列表/站点元数据中的重复卡与错误中文名。

动作：
  1. index.html 网格：删 bitu/qiqihar/karakax/yuxian 4 张卡；
     yuzhou 卡CN 亳州→禹州；fuzhou 福州市→福州；suzhou 苏州市→苏州
  2. cities.html：删对应 <li>；yuzhou 行 亳州→禹州
  3. yuzhou.html：页内唯一 1 处 亳州→禹州
  4. karakax.html：robots→noindex, follow；canonical→hoting.html
  5. yuxian.html：robots→noindex, follow；canonical→yuxi.html
  6. sitemap.xml：删 karakax、yuxian 两个 <url> 块
  7. 探测 prices.html 中 karakax/yuxian 块结构（只打印，不动）
  8. 附带核查 yulin/yichun 卡片CN vs 页面正文省份（只打印）
"""
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DROP = ["bitu", "qiqihar", "karakax", "yuxian"]


def rd(f):
    return open(os.path.join(SITE, f), encoding="utf-8").read()


def wr(f, h):
    open(os.path.join(SITE, f), "w", encoding="utf-8").write(h)


def main():
    # ---------- 1. index.html ----------
    h = rd("index.html")
    n0 = h.count('city-card-wrapper')
    for s in DROP:
        pat = re.compile(
            r'<div class="city-card-wrapper">\s*<a class="city-card" href="%s\.html".*?</a>\s*</div>' % s, re.S)
        h, n = pat.subn("", h)
        print("index.html 撤卡 %-9s %d 处" % (s, n))

    def fix_cn(h, slug, old, new):
        pat = re.compile(
            r'(city-card" href="%s\.html".*?city-card-name-cn">)%s(</span>)' % (slug, old), re.S)
        h, n = pat.subn(r"\g<1>%s\g<2>" % new, h)
        print("index.html 卡 %-9s %s→%s %d 处" % (slug, old, new, n))
        return h

    h = fix_cn(h, "yuzhou", "亳州", "禹州")
    h = fix_cn(h, "fuzhou", "福州市", "福州")
    h = fix_cn(h, "suzhou", "苏州市", "苏州")
    n1 = h.count('city-card-wrapper')
    print("index.html wrapper: %d → %d" % (n0, n1))
    wr("index.html", h)

    # ---------- 2. cities.html ----------
    h = rd("cities.html")
    for s in DROP:
        pat = re.compile(r'<li><a href="%s\.html">.*?</a></li>' % s, re.S)
        h, n = pat.subn("", h)
        print("cities.html 删 %-9s %d 处" % (s, n))
    h, n = re.subn(r'(<a href="yuzhou\.html">)亳州', r"\g<1>禹州", h)
    h, n2 = re.subn(r'(<a href="yuzhou\.html"><span class="cname">)亳州', r"\g<1>禹州", h)
    print("cities.html yuzhou 亳州→禹州 %d+%d 处" % (n, n2))
    wr("cities.html", h)

    # ---------- 3. yuzhou.html ----------
    h = rd("yuzhou.html")
    i = h.find("亳州")
    print("yuzhou.html 亳州 上下文: %s" % re.sub(r"\s+", " ", h[max(0, i - 80):i + 80]))
    h = h.replace("亳州", "禹州")
    wr("yuzhou.html", h)

    # ---------- 4/5. karakax / yuxian 元数据 ----------
    for slug, canon in [("karakax", "hoting"), ("yuxian", "yuxi")]:
        h = rd(slug + ".html")
        h, a = re.subn(r'(<meta name="robots" content=")[^"]*(")', r"\g<1>noindex, follow\g<2>", h)
        h, b = re.subn(r'(<link rel="canonical" href=")[^"]*(")',
                       r"\g<1>https://www.chinawheely.com/%s.html\g<2>" % canon, h)
        print("%s.html robots %d 处 / canonical→%s %d 处" % (slug, a, canon, b))
        wr(slug + ".html", h)

    # ---------- 6. sitemap.xml ----------
    h = rd("sitemap.xml")
    for s in ["karakax", "yuxian"]:
        pat = re.compile(r'\s*<url>\s*<loc>[^<]*%s\.html</loc>.*?</url>' % s, re.S)
        h, n = pat.subn("", h)
        print("sitemap.xml 删 %-9s %d 处" % (s, n))
    wr("sitemap.xml", h)

    # ---------- 7. prices.html 结构探测 ----------
    h = rd("prices.html")
    for s in ["karakax", "yuxian", "yuzhou"]:
        i = h.find('href="%s.html"' % s)
        print("\nprices.html %s 首次出现（前120后60）: %s" % (
            s, re.sub(r"\s+", " ", h[max(0, i - 120):i + 60])))
        m = re.search(r'id="%s"' % s, h)
        if m:
            j = m.start()
            print("prices.html id=%s 块开头: %s" % (s, re.sub(r"\s+", " ", h[j:j + 150])))

    # ---------- 8. yulin/yichun 核查 ----------
    print("\n=== 卡片CN vs 页面正文省份核查 ===")
    ih = rd("index.html")
    gi = ih.find('<div class="grid grid-4">')
    ge = ih.find("</section>", gi)
    d = {}
    for s, e, c in re.findall(
            r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
            r'\s*<span class="city-card-name-cn">([^<]+)</span>', ih[gi:ge], re.S):
        d[s] = c.strip()
    for s in ["yulin", "yulin_sx", "yichun", "yichun_hlj", "taizhou",
              "taizhou_js", "jian", "jining", "yuzhou"]:
        p = os.path.join(SITE, s + ".html")
        if not os.path.exists(p):
            print("   %-11s 无页面" % s)
            continue
        t = open(p, encoding="utf-8", errors="replace").read()
        prov = ""
        m = re.search(r"([A-Za-z ]{3,18}) Province", t)
        if m:
            prov = m.group(1).strip()
        print("   %-11s 卡CN=%-6s 页面省份线索=%s" % (s, d.get(s, "?"), prov))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

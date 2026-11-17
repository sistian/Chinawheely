#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正 cities.html 的城市计数与 JSON-LD ItemList（只统计 prov-sec 区块内的城市）"""
import re, os

REPO = "/Users/w/Desktop/Chinawheely 10.27"
SITE = "https://www.chinawheely.com"
p = os.path.join(REPO, "cities.html")
h = open(p, encoding="utf-8").read()

secs = re.findall(r'<section class="prov-sec" id="prov-[^"]*">(.*?)</section>', h, re.S)
items = []
seen = set()
for s in secs:
    for m in re.finditer(r'<li><a href="([a-z0-9_]+)\.html"><span class="cname">([^<]*)</span><span class="cen">([^<]*)</span></a></li>', s):
        if m.group(1) in seen:
            continue
        seen.add(m.group(1))
        items.append((m.group(1), m.group(3)))

n = len(items)
h = re.sub(r"All \d+ Cities in China", "All %d Cities in China" % n, h)
il = ", ".join('{"@type": "ListItem", "position": %d, "name": "%s", "url": "%s/%s.html"}' % (i, en, SITE, s)
               for i, (s, en) in enumerate(items, 1))
h = re.sub(r'(\{"@context": "https://schema.org", "@type": "ItemList", "itemListElement": )\[.*?\](\})',
           lambda m: m.group(1) + "[" + il + "]" + m.group(2), h, count=1, flags=re.S)
open(p, "w", encoding="utf-8").write(h)
print("cities.html: 城市数 %d，ItemList 已重排" % n)
print("h1 ->", re.search(r"<h1>[^<]*</h1>", h).group(0))

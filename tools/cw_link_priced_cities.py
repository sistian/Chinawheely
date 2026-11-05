#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 prices.html 的每个有价城市块补一个指向该城市页的链接（幂等）
问题：prices.html 只给了 booking.html 的 CTA，没链接到城市页本身，
     导致 53 个有价城市页在站内少一个入链来源（taizhou/zhongshan/zhuhai
     因此只剩 index.html 一个来源 → 弱内链）。
修法：在每个 <details class="city" data-slug="X"> 里加一条
     “X city guide →” 链接到 X.html
"""
import os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

h = open('prices.html', encoding='utf-8').read()
n = 0
out = []
pos = 0
for m in re.finditer(r'<details class="city" data-slug="([a-zA-Z0-9_\-]+)"[^>]*data-en="([^"]+)"',
                     h):
    slug, en = m.group(1), m.group(2)
    if f'href="{slug}.html"' in h[m.end():h.find('</details>', m.end())]:
        continue                      # 已有链接
    block_end = h.find('</details>', m.end())
    seg = h[m.end():block_end]
    link = f'<a class="city-guide-link" href="{slug}.html">{en} city guide &rarr;</a> '
    # 插到 book-cta 之前
    b = seg.find('<a class="book-cta"')
    if b >= 0:
        abs_b = m.end() + b
        h = h[:abs_b] + link + h[abs_b:]
        n += 1
    else:
        continue

if n:
    open('prices.html', 'w', encoding='utf-8').write(h)
print(f'prices.html: 给 {n} 个有价城市补了城市页链接')

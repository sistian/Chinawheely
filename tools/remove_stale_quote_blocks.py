#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
331 城全覆盖后：把「已定价但仍挂着 CW:QUOTE-BLOCK 询价区块」的城市页清理掉。
（这些城市将由 apply_price_showcase.py 插入真实价目表 CW:PRICE-LIST）
"""
import json, os, re, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, 'pricing', 'pricing.json'), encoding='utf-8'))
priced = set(d['cities'])

removed = skipped = 0
for fn in sorted(glob.glob(os.path.join(BASE, '*.html'))):
    slug = os.path.basename(fn)[:-5]
    h = open(fn, encoding='utf-8').read()
    if 'CW:QUOTE-BLOCK' not in h:
        continue
    new = re.sub(r'<!-- CW:QUOTE-BLOCK -->.*?<!-- /CW:QUOTE-BLOCK -->\s*\n?', '', h, flags=re.S)
    if new == h:
        continue
    if slug not in priced:
        skipped += 1  # 无价城市保留询价区块
        continue
    open(fn, 'w', encoding='utf-8').write(new)
    removed += 1

print(f'移除询价区块: {removed} 页；保留（无价）: {skipped} 页')

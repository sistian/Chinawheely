#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建已插入的 CW:PRICE-LIST 区块（修正实体二次转义等），幂等"""
import os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

MARK = "<!-- CW:PRICE-LIST -->"
END = "<!-- /CW:PRICE-LIST -->"

import apply_price_showcase as A

n = 0
for fn in sorted(os.listdir(BASE)):
    if not fn.endswith(".html"):
        continue
    slug = fn[:-5]
    c = A.city_of(slug)
    if not c:
        continue
    p = os.path.join(BASE, fn)
    s = open(p, encoding="utf-8").read()
    if MARK not in s:
        continue
    i = s.find(MARK)
    j = s.find(END, i)
    if j < 0:
        print("跳过（无结束标记）:", fn)
        continue
    new_block = A.build_price_section(c)
    s = s[:i] + new_block + s[j + len(END):]
    open(p, "w", encoding="utf-8").write(s)
    n += 1
print(f"重建 {n} 页")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建已插入的 CW:QUOTE-BLOCK 区块（修正城市名抽取等），幂等"""
import os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

MARK = "<!-- CW:QUOTE-BLOCK -->"
END = "<!-- /CW:QUOTE-BLOCK -->"

import apply_quote_blocks as Q

samples = Q.pick_samples()
n = 0
for fn in sorted(os.listdir(BASE)):
    if not fn.endswith(".html"):
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
    city_en = Q.city_name_from_html(s)
    if not city_en:
        print("跳过（无城市名）:", fn)
        continue
    city_cn = ""
    m = re.search(r'"name":\s*"([^"]+)"', s)
    if m:
        city_cn = m.group(1)
    block = Q.build_quote_block(city_en, city_cn, samples)
    s = s[:i] + block + s[j + len(END):]
    open(p, "w", encoding="utf-8").write(s)
    n += 1
print(f"重建 {n} 页")

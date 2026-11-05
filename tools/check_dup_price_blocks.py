#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查带报价区块的页面之间是否有近重复（防止 280 页内容雷同被降权）"""
import os, re, random
from itertools import combinations

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def toks(p):
    s = open(p, encoding="utf-8", errors="ignore").read()
    s = re.sub(r"<script.*?</script>", "", s, flags=re.S)
    s = re.sub(r"<style.*?</style>", "", s, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", s)
    return set(re.findall(r"[a-z]{4,}", t.lower()))


files = []
for f in sorted(os.listdir(BASE)):
    if not f.endswith(".html"):
        continue
    s = open(os.path.join(BASE, f), encoding="utf-8", errors="ignore").read()
    if "CW:QUOTE-BLOCK" in s or "CW:PRICE-LIST" in s:
        files.append(f)

print(f"含价格区块的页: {len(files)}")
random.seed(1)
sample = random.sample(files, min(50, len(files)))
ts = {f: toks(os.path.join(BASE, f)) for f in sample}
pairs = []
for a, b in combinations(sample, 2):
    ta, tb = ts[a], ts[b]
    if not ta or not tb:
        continue
    j = len(ta & tb) / len(ta | tb)
    if j > 0.75:
        pairs.append((round(j, 3), a, b))
pairs.sort(reverse=True)
print(f"近重复页对 (>0.75 Jaccard): {len(pairs)}")
for p in pairs[:12]:
    print("  ", p)

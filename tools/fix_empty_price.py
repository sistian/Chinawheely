#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复空价格 span（'From ' 后面什么都没有），改为 Quote on request"""
import os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = re.compile(
    r'(<span style="font-size:var\(--text-2xl\);color:var\(--color-primary\);font-weight:700;">)\s*From\s*(</span>)')

n = 0
for fn in sorted(os.listdir(BASE)):
    if not fn.endswith(".html"):
        continue
    p = os.path.join(BASE, fn)
    s = open(p, encoding="utf-8").read()
    if not PAT.search(s):
        continue
    s2 = PAT.sub(r'\1Quote on request\2', s)
    open(p, "w", encoding="utf-8").write(s2)
    c = len(PAT.findall(s))
    print(f"  {fn}: 修复 {c} 处")
    n += c
print(f"共修复 {n} 处空价格")

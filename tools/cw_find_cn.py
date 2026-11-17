#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查找站点内含特定中文串的所有位置及上下文（用于人工核对身份矛盾）。

用法： python3 tools/cw_find_cn.py 建阳
"""
import os
import re
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
needle = sys.argv[1]
pat = re.compile(re.escape(needle))
for fn in sorted(os.listdir(SITE)):
    if not fn.endswith(".html"):
        continue
    p = os.path.join(SITE, fn)
    h = open(p, encoding="utf-8", errors="replace").read()
    for m in pat.finditer(h):
        s = max(0, m.start() - 70)
        e = min(len(h), m.end() + 70)
        ctx = h[s:e].replace("\n", " ")
        print("%-22s ...%s..." % (fn, ctx))

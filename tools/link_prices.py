#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P3 收尾 —— 全站 footer「Services」列表加入 Prices 链接 + nav 链接检查
用法: python3 tools/link_prices.py [--dry]
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = "--dry" in sys.argv
TARGET = '<li><a href="services.html#intercity">Intercity Trips</a></li>'
ADD = '\n<li><a href="prices.html">Published Prices</a></li>'

count = 0
files = [f for f in os.listdir(BASE) if f.endswith(".html")]
for f in files:
    p = os.path.join(BASE, f)
    s = open(p, encoding="utf-8").read()
    if "prices.html" in s:
        continue  # 已有链接（如 prices 自身 / 新页）
    if TARGET not in s:
        continue
    s2 = s.replace(TARGET, TARGET + ADD, 1)
    if s2 != s:
        count += 1
        if not DRY:
            open(p, "w", encoding="utf-8").write(s2)
print(f"footer 加 Prices 链接: {count} 个文件")

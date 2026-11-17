#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查报价单 xlsx 里有哪些城市 —— 与站点现有页面/定价对比，
找出「报价单有、站点没有页面」的城市（= 扩城优先级信号）。

用法： python3 tools/cw_xlsx_city_coverage.py
"""
import json
import os
import re

import openpyxl

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "/Users/w/Desktop/入境游包车报价单_游客版 2026年 报价单 更新版本.xlsx"
PRICING = os.path.join(BASE, "pricing", "pricing.json")

wb = openpyxl.load_workbook(SRC, data_only=True)
print("工作表:", wb.sheetnames)

names = []
for ws in wb.worksheets:
    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 40), max_col=4,
                            values_only=True):
        for v in row:
            if isinstance(v, str):
                for cn, en in re.findall(r"([一-鿿]{2,6})\s*[（(]?([A-Za-z][A-Za-z \-']{2,20})[)）]?", v):
                    names.append((cn.strip(), en.strip(), ws.title))
                    break
        break

cn_names = []
for ws in wb.worksheets:
    for row in ws.iter_rows(values_only=True):
        for v in row:
            if isinstance(v, str) and re.search(r"[一-鿿]", v) and not re.search(r"[A-Za-z]{4,}", v):
                s = v.strip()
                if 2 <= len(s) <= 8 and " " not in s:
                    cn_names.append((s, ws.title))
                    break

print("表格中出现的中文词条(去重):", len(set(cn_names)))
seen = []
for c, ws in cn_names:
    if c not in [x[0] for x in seen]:
        seen.append((c, ws))

# 站点中文名
h = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
gi = h.find('<div class="grid grid-4">')
ge = h.find("</section>", gi)
site_cn = set(re.findall(r'city-card-name-cn">([^<]+)</span>', h[gi:ge]))

# pricing.json
pj = json.load(open(PRICING, encoding="utf-8"))
priced = set(pj.get("cities", {}).keys()) if isinstance(pj.get("cities"), dict) else set()

print("\n== 报价单里出现、但站点没有同名卡片的条目 ==")
n = 0
for c, ws in seen:
    if c in site_cn:
        continue
    n += 1
    print("  %-10s [%s]" % (c, ws))
print("共", n, "条")

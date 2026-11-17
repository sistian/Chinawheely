#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出报价单 xlsx 里全部城市（列 A「中文 English」），并与站点页面/定价对照。

用法： python3 tools/cw_xlsx_cities.py
"""
import json
import os
import re

import openpyxl

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "/Users/w/Desktop/入境游包车报价单_游客版 2026年 报价单 更新版本.xlsx"

wb = openpyxl.load_workbook(SRC, data_only=True)
ws = wb["各种车型接送机报价"]
rows = []
for r in range(3, ws.max_row + 1):
    v = ws.cell(row=r, column=1).value
    if not isinstance(v, str) or not v.strip():
        continue
    rows.append((r, v.strip()))
print("报价单城市行数:", len(rows))

site_cn = set()
h = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
gi = h.find('<div class="grid grid-4">')
ge = h.find("</section>", gi)
for cn in re.findall(r'city-card-name-cn">([^<]+)</span>', h[gi:ge]):
    site_cn.add(cn.strip().rstrip("市"))

pj = json.load(open(os.path.join(BASE, "pricing", "pricing.json"), encoding="utf-8"))
priced_cities = pj.get("cities", {})
priced_cn = set()
if isinstance(priced_cities, dict):
    for slug, v in priced_cities.items():
        cn = v.get("cn") if isinstance(v, dict) else None
        if cn:
            priced_cn.add(cn.strip().rstrip("市"))

print("\n== 报价单有、但站点没有城市页的中文名 ==")
miss = []
for r, v in rows:
    cn = re.split(r"[\s(（]", v)[0].strip().rstrip("市")
    if cn and cn not in site_cn:
        miss.append((r, v))
for r, v in miss:
    print("  row %-4s %s" % (r, v))
print("共", len(miss))

print("\n== 站点有页面但报价单里没有 ==")
xlsx_cn = set(re.split(r"[\s(（]", v)[0].strip().rstrip("市") for _, v in rows)
only_site = sorted(c for c in site_cn if c not in xlsx_cn)
print(" ", "、".join(only_site))
print("共", len(only_site))

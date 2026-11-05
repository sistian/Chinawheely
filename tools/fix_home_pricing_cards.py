#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P5c —— 首页「Transparent Pricing」卡片去占位化

原卡片写的是 From $50 / $80 / $105，与报价单完全无关（也是假价）。
改法：换成报价单真实数字。
  · 每张卡用该车型在 53 个已公布城市里的最低价（真实可查）
  · 同时给出价格区间，让用户知道上限
  · 美元按 1 USD = 7.10 换算，人民币为主

用法: python3 tools/fix_home_pricing_cards.py
"""
import html
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, "pricing", "pricing.json"), encoding="utf-8"))
C = d["cities"]
R = d["meta"]["usdCnyRate"]

CARDS = [
    ("pricing-name\">\n Economy", "sedan_economy",
     "Sedan &middot; Up to 3 passengers &middot; 35 km included"),
    ("pricing-name\">\n Business", "sedan_comfort",
     "Premium Sedan &middot; Up to 3 passengers &middot; 35 km included"),
    ("pricing-name\">\n MPV / Van", "mpv_6",
     "Up to 6 passengers &middot; Extra luggage &middot; 35 km included"),
]

path = os.path.join(BASE, "index.html")
s = open(path, encoding="utf-8").read()
orig = s

for marker, key, desc in CARDS:
    vals = [c["airport"][key]["pkg"] for c in C.values()]
    lo, hi = min(vals), max(vals)
    lo_usd, hi_usd = round(lo / R, 2), round(hi / R, 2)
    price_html = (f'From &yen;{lo} <span class="pricing-usd">(&asymp; ${lo_usd})</span>'
                  f'<span class="pricing-range">&yen;{lo}&ndash;&yen;{hi} '
                  f'(&asymp; ${lo_usd}&ndash;${hi_usd}) across our 53 published cities</span>')

    i = s.find(marker)
    if i < 0:
        print("  未找到卡片:", marker)
        continue
    # 该卡片的 desc 与 price 容器
    dpos = s.find("pricing-desc", i)
    ppos = s.find("pricing-price", i)
    if dpos < 0 or ppos < 0:
        print("  卡片结构异常:", marker)
        continue

    # desc：把 &middot; 后面换成真实说明
    dend = s.find("</div>", dpos)
    new_desc = (f'<div class="pricing-desc">{desc} &middot; all fees included</div>')
    s = s[:dpos] + new_desc + s[dend:]

    # price 容器内内容整体替换（容器是 <div class="pricing-price"> ... </div>，
    # 内部可能还有嵌套 span，需配对匹配）
    ppos = s.find('class="pricing-price"', i)
    if ppos < 0:
        print("  未找到 pricing-price:", marker)
        continue
    open_tag_end = s.find(">", ppos) + 1
    # 从 open_tag_end 起做标签配平，找到 pricing-price 的真正结束位置
    depth = 1
    k = open_tag_end
    while k < len(s) and depth > 0:
        m2 = re.compile(r"</?div\b[^>]*>").search(s, k)
        if not m2:
            break
        if m2.group(0).startswith("</"):
            depth -= 1
        else:
            depth += 1
        k = m2.end()
    s = s[:open_tag_end] + price_html + s[k - len("</div>"):]

if s != orig:
    open(path, "w", encoding="utf-8").write(s)
    print("首页价格卡片已更新为报价单真实数字")
else:
    print("首页价格卡片无需改动")

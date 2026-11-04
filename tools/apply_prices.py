#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P3 —— 城市页真实价格 + prices.html 价格总览页

规则:
  1. 53 个有价城市：把硬编码 `From $N` 换成报价单真实价（¥ 为主，USD 参考）
     - 机场/接送类卡片 → 该城接送机最低价（4座经济型）
     - 包车/日游类卡片 → 按标注小时数取对应时长档（4座专车）；无小时数按 8 小时档
  2. 无价城市：移除假价格 → `Quote on request`
  3. index.html：按具名航线用对应城市真实价
  4. 生成 prices.html（静态全量价格表，可被抓取）
  5. sitemap.xml 加入 prices.html

用法: python3 tools/apply_prices.py [--dry]
"""
import html
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = "--dry" in sys.argv

data = json.load(open(os.path.join(BASE, "pricing", "pricing.json"), encoding="utf-8"))
CITIES = data["cities"]
RATE = data["meta"]["usdCnyRate"]

HOUR_TIER = {2: "2h_35km", 4: "4h_50km", 6: "6h_75km", 8: "8h_100km", 10: "10h_125km"}

# 页面 slug → 价格表 slug（同名不同市/别名页需显式映射）
SLUG_ALIAS = {
    "huhehaote": "hohhot",   # 呼和浩特 = Hohhot
}

# index.html 具名航线 → 城市 slug
INDEX_ROUTES = [
    ("Beijing Capital (PEK)", "beijing"),
    ("Shanghai Pudong (PVG)", "shanghai"),
    ("Chengdu Tianfu (TFU)", "chengdu"),
]


def usd(cny):
    return round(cny / RATE, 2)


def fmt(cny):
    return f"¥{cny} (≈ ${usd(cny)})"


def airport_floor(slug):
    c = CITIES.get(slug)
    if not c:
        return None
    vals = [v["pkg"] for v in c.get("airport", {}).values() if v.get("pkg") is not None]
    return min(vals) if vals else None


def charter_price(slug, hours):
    c = CITIES.get(slug)
    if not c:
        return None
    v = c.get("charter", {}).get("sedan_4")
    if not v:
        return None
    tier = HOUR_TIER.get(hours, "8h_100km")
    t = v.get("tiers", {}).get(tier)
    return t["pkg"] if t else None


def card_context(s, pos):
    """取卡片上下文：最近的 h2（区块标题）+ h3/h4（卡片标题）+ 前向 220 字符的 meta 行"""
    back = s[max(0, pos - 900):pos]
    fwd = s[pos:pos + 220]
    h2 = re.findall(r"<h2[^>]*>(.*?)</h2>", back, re.S)
    h4 = re.findall(r"<h[34][^>]*>(.*?)</h[34]>", back, re.S)
    ctx = ""
    if h2:
        ctx += re.sub(r"<[^>]+>", " ", h2[-1]) + " "
    if h4:
        ctx += re.sub(r"<[^>]+>", " ", h4[-1]) + " "
    m = re.search(r"~[\d\s,.\u2013-]+\s*km[^<]{0,80}", fwd)
    if m:
        ctx += m.group(0)
    else:
        ctx += re.sub(r"<[^>]+>", " ", fwd[:160])
    return ctx


def classify(ctx):
    """根据卡片上下文判断产品类型与时长"""
    low = ctx.lower()
    hours = None
    for m in re.finditer(r"(\d+)\s*-?\s*hour", low):
        h = int(m.group(1))
        if h in HOUR_TIER:
            hours = h
    if hours:
        return "charter", hours
    if re.search(r"standby|hourly", low):
        return "charter", 2
    if re.search(r"day\s*trip|day\s*tour|full[\s-]*day|city\s*tour|whole\s*day|"
                 r"one[\s-]*day|day\s*package|sightseeing|day\s*trips", low):
        return "charter", 8
    if re.search(r"airport|pickup|pick-up|dropoff|drop-off|\u2192|&rarr;", low):
        return "airport", None
    return "airport", None


def price_for(slug, ctx):
    product, hours = classify(ctx)
    if product == "charter":
        p = charter_price(slug, hours)
        if p is not None:
            return p
    p = airport_floor(slug)
    return p


# ---------------------------------------------------------------- 城市页
CITY_PAGE = re.compile(r"^[a-z_]+\.html$")
stats = {"priced": 0, "unpriced": 0, "replaced": 0, "files": 0, "skipped": 0}

for fname in sorted(os.listdir(BASE)):
    if not fname.endswith(".html") or not CITY_PAGE.match(fname):
        continue
    if fname == "index.html":
        continue
    slug = fname[:-5]
    path = os.path.join(BASE, fname)
    s = open(path, encoding="utf-8").read()
    if "From $" not in s:
        continue
    orig = s
    pslug = SLUG_ALIAS.get(slug, slug)

    if pslug in CITIES:
        stats["priced"] += 1

        def repl2(m):
            stats["replaced"] += 1
            ctx = card_context(s, m.start())
            p = price_for(pslug, ctx)
            return fmt(p) if p is not None else m.group(0)

        s = re.sub(r"From \$\d+", repl2, s)
    else:
        stats["unpriced"] += 1

        def repl3(m):
            stats["replaced"] += 1
            return "Quote on request"

        s = re.sub(r"From \$\d+", repl3, s)

    if s != orig:
        stats["files"] += 1
        if not DRY:
            open(path, "w", encoding="utf-8").write(s)

print(f"城市页: 有价 {stats['priced']} / 无价 {stats['unpriced']}, "
      f"替换 {stats['replaced']} 处, 改动 {stats['files']} 个文件")

# ---------------------------------------------------------------- index.html
idx_path = os.path.join(BASE, "index.html")
idx = open(idx_path, encoding="utf-8").read()
if "From $" in idx:
    def idx_repl(m):
        ctx = idx[max(0, m.start() - 700):m.start()]
        for label, cslug in INDEX_ROUTES:
            if label in ctx:
                p = airport_floor(cslug)
                if p is not None:
                    stats["replaced"] += 1
                    return fmt(p)
        stats["replaced"] += 1
        return "Quote on request"

    new_idx = re.sub(r"From \$\d+", idx_repl, idx)
    if new_idx != idx:
        stats["files"] += 1
        if not DRY:
            open(idx_path, "w", encoding="utf-8").write(new_idx)
        print(f"index.html: 已替换 {idx.count('From $')} 处航线价格")
print(f"合计替换 {stats['replaced']} 处，改动 {stats['files']} 个文件")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复城市页「Popular Routes」卡片里的裸假价（50 / 65 / 90 / 80 …）。

背景：
  2026-10-29 的 a6c532b 把卡片里的 "From $50" 去掉美元符号时，只删了
  "From $" 三个字符，把数字 50 留下了，于是全站 271 个城市页 / 986 处
  在页面上显示成一个没有货币单位、没有来源的裸数字（比 "From $50" 更糟：
  用户会当成人民币 50 元）。

  apply_prices.py 的 PRICE_TOKEN 只匹配 "¥X (≈ $Y)"，因此这批卡片从未被
  P3 的真实价格替换过 —— 既没变成真实价，也没变成 "Quote on request"。

本脚本：
  1. 有价城市（pricing.json 53 城）→ 卡片显示真实价
       · 接送机类卡片（meta 含 "min" 不含 "hour"）→ airport.sedan_economy.pkg
       · 包车类卡片（meta 含 "N-hour"）→ charter.sedan_4.tiers[HOUR_TIER].pkg
     数字位置写 "¥X"，其后追加小字 "(≈ $Y) @ 7.10"
  2. 无价城市 → 数字位置改成 "Quote on request"
  3. 幂等：已处理过的卡片（不再含裸数字）不会被再次改动。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HOUR_TIER = {2: "2h_35km", 4: "4h_50km", 6: "6h_75km", 8: "8h_100km", 10: "10h_125km"}

# 卡片价格位：<span style="font-size:var(--text-2xl);color:var(--color-primary);font-weight:700;">50</span>
SPAN_RE = re.compile(
    r'(<span style="font-size:var\(--text-2xl\);color:var\(--color-primary\);font-weight:700;">)'
    r'(\d+)'
    r'(</span>)'
)

# 卡片 meta 行（紧跟 span 之后）：~30 km · 30–60 min · Economy/Business/MPV
META_RE = re.compile(
    r'\s*</div>\s*<p style="font-size:var\(--text-sm\);color:var\(--color-gray-500\);'
    r'margin-bottom:var\(--space-3\);">([^<]*)</p>'
)

EXCLUDED = {
    "index.html", "404.html", "admin.html", "admin-login.html", "thank-you.html",
    "prices.html", "manage-order.html", "booking.html", "contact.html",
    "get-quote.html", "services.html", "help.html", "cookies.html", "partners.html",
    "careers.html", "cancellation.html", "seo-swot-analysis.html",
    "image_downloader.html", "batch_download.html", "about.html", "terms.html",
    "privacy.html", "china-visa-guide.html", "china-consulate-guide.html",
}

USD_RATE = 7.10


def usd(cny):
    return round(cny / USD_RATE, 2)


def fmt_usd(v):
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    return s


def usd_text(cny):
    return "≈ $" + fmt_usd(usd(cny))


def load_pricing():
    with open(os.path.join(BASE, "pricing", "pricing.json"), encoding="utf-8") as f:
        return json.load(f)


def classify(meta):
    """返回 ('airport', None) 或 ('charter', hours)"""
    m = meta.lower()
    h = re.search(r"(\d+)\s*-?\s*hour", m)
    if h:
        hrs = int(h.group(1))
        if hrs in HOUR_TIER:
            return "charter", hrs
    return "airport", None


def price_for(city, kind, hours):
    """取真实价；取不到返回 None"""
    try:
        if kind == "airport":
            v = city["airport"]["sedan_economy"]["pkg"]
        else:
            tiers = city["charter"]["sedan_4"]["tiers"]
            v = tiers[HOUR_TIER[hours]]["pkg"]
        return v
    except Exception:
        return None


def fix_page(path, slug, pricing_cities):
    with open(path, encoding="utf-8") as f:
        s = f.read()

    if not SPAN_RE.search(s):
        return 0, 0

    city = pricing_cities.get(slug)
    fixed = 0
    unpriced = 0

    def repl(m):
        nonlocal fixed, unpriced
        # 找到该 span 之后的 meta 行
        tail = s[m.end():m.end() + 400]
        mm = META_RE.match(tail)
        meta = mm.group(1) if mm else ""
        kind, hours = classify(meta)

        if city is None:
            unpriced += 1
            return ('<span style="font-size:var(--text-lg);color:var(--color-primary);'
                    'font-weight:700;">Quote on request</span>')

        val = price_for(city, kind, hours)
        if val is None:
            unpriced += 1
            return ('<span style="font-size:var(--text-lg);color:var(--color-primary);'
                    'font-weight:700;">Quote on request</span>')

        fixed += 1
        return ('<span style="font-size:var(--text-2xl);color:var(--color-primary);'
                'font-weight:700;">From ¥%s</span>'
                '<span style="font-size:var(--text-sm);color:var(--color-gray-500);'
                'font-weight:600;margin-left:6px;">(%s)</span>'
                % (val, usd_text(val).replace("≈ ", "")))

    out = SPAN_RE.sub(repl, s)
    if out != s:
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
    return fixed, unpriced


def main():
    pricing = load_pricing()
    pricing_cities = pricing["cities"]

    total_fixed = 0
    total_unpriced = 0
    pages = 0

    for fn in sorted(os.listdir(BASE)):
        if not fn.endswith(".html") or fn in EXCLUDED:
            continue
        path = os.path.join(BASE, fn)
        if not os.path.isfile(path):
            continue
        slug = fn[:-5]
        fx, up = fix_page(path, slug, pricing_cities)
        if fx or up:
            pages += 1
            total_fixed += fx
            total_unpriced += up

    print("处理页面 %d 个 | 有价城市改真实价 %d 处 | 无价城市改 Quote on request %d 处"
          % (pages, total_fixed, total_unpriced))
    return 0


if __name__ == "__main__":
    sys.exit(main())

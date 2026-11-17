#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交叉核对（修正版）：首页卡片 ↔ cities.html JSON-LD ↔ prices.html。

用法： python3 tools/cw_crossref_names.py
"""
import json
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUF = ("市", "地区", "自治州", "盟", "县", "区")


def norm(s):
    s = (s or "").strip()
    for x in SUF:
        if s.endswith(x) and len(s) > len(x):
            s = s[: -len(x)]
            break
    return s


def index_cards():
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    pairs = re.findall(
        r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
        r'\s*<span class="city-card-name-cn">([^<]+)</span>', h[gi:ge], re.S)
    return {s: (en, cn) for s, en, cn in pairs}


def ld_blocks(fn):
    h = open(os.path.join(SITE, fn), encoding="utf-8").read()
    out = []
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', h, re.S | re.I):
        out.append(m.group(1))
    return out


def jsonld_items(fn):
    items = []
    for blob in ld_blocks(fn):
        try:
            d = json.loads(blob.strip())
        except Exception:
            # 可能是多段 JSON 或尾部逗号
            continue
        for it in walk(d):
            if isinstance(it, dict) and it.get("@type") == "ListItem" and it.get("url"):
                slug = it["url"].rsplit("/", 1)[-1].replace(".html", "")
                items.append((slug, it.get("name", ""), it.get("position")))
    return items


def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


def prices_blocks():
    h = open(os.path.join(SITE, "prices.html"), encoding="utf-8").read()
    return [(m.group(1), m.group(2), m.group(3)) for m in
            re.finditer(r'data-slug="([a-z_0-9]+)"\s+data-cn="([^"]*)"\s+data-en="([^"]*)"', h)]


def main():
    cards = index_cards()
    print("首页卡片:", len(cards))
    problems = []

    items = jsonld_items("cities.html")
    print("cities.html JSON-LD ListItem:", len(items))
    seen = {}
    for slug, name, pos in items:
        seen.setdefault(slug, []).append((name, pos))
    for slug, lst in seen.items():
        cn = cards.get(slug, (None, None))[1]
        if len(lst) > 1:
            problems.append(("JSON-LD 重复 slug", slug, lst))
        if cn and norm(lst[0][0]) != norm(cn):
            problems.append(("JSON-LD 名不符", slug, "%s vs 卡片 %s" % (lst[0][0], cn)))
    for slug, (en, cn) in cards.items():
        if slug not in seen:
            problems.append(("JSON-LD 缺该城", slug, cn))
    for slug, lst in seen.items():
        if slug not in cards:
            problems.append(("JSON-LD 残留(卡片已无)", slug, lst[0][0]))

    pb = prices_blocks()
    print("prices.html 城市块:", len(pb))
    for slug, cn, en in pb:
        c = cards.get(slug)
        if not c:
            problems.append(("prices 有卡片外城市", slug, "%s/%s" % (cn, en)))
        elif norm(cn) != norm(c[1]):
            problems.append(("prices 中文名不符", slug, "%s vs 卡片 %s" % (cn, c[1])))

    print("\n== 问题 %d ==" % len(problems))
    for p in problems:
        print("  [%s] %-16s %s" % p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

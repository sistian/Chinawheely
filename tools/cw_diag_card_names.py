#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断首页城市卡片的中文名/英文名重复与错配。

输出三类问题：
  1) 同一中文名对应多个 slug（疑似别名页重复）
  2) 同一 slug 在不同页面里被叫不同名字（错配）
  3) 卡片 slug 集合 vs prices.html 城市集合的差集
"""
import os
import re
from collections import defaultdict

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DROP = {"index", "cities", "prices", "booking", "contact", "help", "about",
        "cookies", "services", "partners", "careers", "admin", "cancellation",
        "manage-order", "thank-you", "404"}


def cards():
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    return re.findall(
        r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
        r'\s*<span class="city-card-name-cn">([^<]+)</span>', h[gi:ge], re.S)


def page_meta(slug):
    f = os.path.join(SITE, slug + ".html")
    if not os.path.exists(f):
        return None
    h = open(f, encoding="utf-8", errors="replace").read()
    title = re.search(r"<title>(.*?)</title>", h, re.S)
    robots = re.search(r'<meta name="robots" content="([^"]*)"', h)
    canon = re.search(r'canonical" href="([^"]*)"', h)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    def clean(s):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()
    return {
        "title": clean(title.group(1) if title else ""),
        "robots": robots.group(1) if robots else "",
        "canonical": canon.group(1) if canon else "",
        "h1": clean(h1.group(1) if h1 else ""),
        "h1_cn": (re.search(r"([一-鿿]{2,6})", clean(h1.group(1) if h1 else "")) or [None, ""])[1]
        if h1 else "",
    }


def main():
    cs = cards()
    print("首页卡片:", len(cs), " 唯一 slug:", len(set(c[0] for c in cs)))

    by_cn = defaultdict(list)
    for slug, en, cn in cs:
        by_cn[cn].append((slug, en))
    print("\n=== 中文名重复 ===")
    for cn, v in sorted(by_cn.items()):
        if len(v) > 1:
            print(f"  {cn}: {v}")
            for slug, en in v:
                m = page_meta(slug)
                if m:
                    print(f"      {slug:12s} robots={m['robots']:14s} canon={m['canonical'].split('/')[-1]:16s} h1_cn={m['h1_cn']}")

    by_en = defaultdict(list)
    for slug, en, cn in cs:
        by_en[en].append((slug, cn))
    print("\n=== 英文名重复 ===")
    for en, v in sorted(by_en.items()):
        if len(v) > 1:
            print(f"  {en}: {v}")

    # prices.html 集合差集
    p = open(os.path.join(SITE, "prices.html"), encoding="utf-8").read()
    pcity = set(re.findall(r'href="([a-z_0-9]+)\.html"', p)) - DROP
    cslug = set(c[0] for c in cs)
    print("\n=== 集合差集 ===")
    print("  首页有 / prices 无:", sorted(cslug - pcity))
    print("  prices 有 / 首页无:", sorted(pcity - cslug))

    # 每张卡的中文名 vs 该页 h1 中文名 是否一致
    print("\n=== 卡片中文名 vs 页面 h1 中文名 不一致 ===")
    for slug, en, cn in cs:
        m = page_meta(slug)
        if not m:
            print(f"  {slug:12s} 缺页面")
            continue
        if m["h1_cn"] and m["h1_cn"] != cn:
            print(f"  {slug:12s} 卡片={cn}  页面h1={m['h1_cn']}  ({en})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

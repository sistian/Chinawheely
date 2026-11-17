#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 2026-11-17 交叉核对发现的 9 处数据 bug：
  1) jian.html = Jianyang 简阳（四川），全站 6 处误写「建阳」（福建建阳区）
  2) index.html / cities.html 卡片英文名「Luzhi Water Town Transfer &」截断 → 「Luzhi」
  3) cities.html JSON-LD：yichun 名写成「伊春」（应 宜春）、yuzhou 写成「亳州」（应 禹州）
  4) cities.html JSON-LD：残留 4 个已撤卡城市（bitu/karakax/qiqihar/yuxian），并重排 position
  5) prices.html：yichun 的 data-cn 写成「伊春」（应 宜春）

用法： python3 tools/cw_fix_data_bugs.py [--dry]
"""
import json
import os
import re
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = "--dry" in sys.argv
STALE = {"bitu", "karakax", "qiqihar", "yuxian"}
NAME_FIX = {"yichun": "宜春", "yuzhou": "禹州", "jian": "简阳"}


def read(f):
    return open(os.path.join(SITE, f), encoding="utf-8").read()


def write(f, t):
    open(os.path.join(SITE, f), "w", encoding="utf-8").write(t)


def report(f, before, after, label):
    if before == after:
        print("skip  %-14s %s (无变化)" % (f, label))
        return False
    if not DRY:
        write(f, after)
    print("PATCH %-14s %s" % (f, label))
    return True


def fix_jianyang():
    pats = [
        (r'(<a href="jian\.html">\s*<span class="ln-cn">)建阳(</span>)', r'\1简阳\2'),
        (r'(<a href="jian\.html">\s*<span class="cname">)建阳(</span>)', r'\1简阳\2'),
        (r'(<a href="jian\.html">\s*<span class="city-name">)建阳(</span>)', r'\1简阳\2'),
        (r'(city-card-name-cn">)建阳(</span>)', r'\1简阳\2'),
        (r'(data-slug="jian"\s+data-cn=")建阳(")', r'\1简阳\2'),
        (r'(data-slug="jian"[^>]*>\s*<summary><span class="city-name">)建阳(\s+Jianyang</span>)', r'\1简阳\2'),
        (r'(pl-title">Fixed Price List &mdash; )建阳( \(Jianyang\))', r'\1简阳\2'),
    ]
    for f in ["index.html", "cities.html", "prices.html", "jian.html",
              "changdou.html", "chongqing.html", "yongchuan.html"]:
        if not os.path.exists(os.path.join(SITE, f)):
            continue
        h = read(f)
        o = h
        for p, r in pats:
            h = re.sub(p, r, h)
        report(f, o, h, "jianyang 建阳→简阳")


def fix_luzhi():
    f = "index.html"
    h = read(f)
    o = h
    h = h.replace('<span class="city-card-name">Luzhi Water Town Transfer &</span>',
                  '<span class="city-card-name">Luzhi</span>')
    h = h.replace('alt="Luzhi Water Town Transfer &"', 'alt="Luzhi Water Town"')
    report(f, o, h, "luzhi 卡英文名截断")

    f = "cities.html"
    h = read(f)
    o = h
    h = h.replace('<span class="cen">Luzhi Water Town Transfer &amp;</span>',
                  '<span class="cen">Luzhi</span>')
    report(f, o, h, "luzhi cen 截断")


def fix_cities_jsonld():
    f = "cities.html"
    h = read(f)
    o = h
    m = re.search(r'(<script[^>]*application/ld\+json[^>]*>)(.*?)(</script>)', h, re.S | re.I)
    if not m:
        print("!! cities.html 找不到 JSON-LD")
        return
    d = json.loads(m.group(2).strip())
    node = None
    for g in d.get("@graph", []):
        il = g.get("itemListElement")
        if isinstance(il, list) and il and isinstance(il[0], dict) and "url" in il[0]:
            node = g   # 只要带 url 的城市 ItemList（不要 BreadcrumbList）
    if node is None:
        print("!! cities.html JSON-LD 无 itemListElement")
        return
    items = node["itemListElement"]
    kept = []
    for it in items:
        slug = it.get("url", "").rsplit("/", 1)[-1].replace(".html", "")
        if slug in STALE:
            continue
        if slug in NAME_FIX:
            it["name"] = NAME_FIX[slug]
        kept.append(it)
    for i, it in enumerate(kept, 1):
        it["position"] = i
    node["itemListElement"] = kept
    # 城市数量文案同步
    blob = json.dumps(d, ensure_ascii=False, indent=2)
    h = h[:m.start(2)] + "\n" + blob + "\n" + h[m.end(2):]
    report(f, o, h, "JSON-LD 清理残留 %d 项 + 名字修正 + position 重排 (剩 %d)" % (len(items) - len(kept), len(kept)))

    mm = re.search(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', h, re.S | re.I)
    try:
        dd = json.loads(mm.group(1).strip())
        n = sum(len(g.get("itemListElement", [])) for g in dd.get("@graph", [])
                if isinstance(g.get("itemListElement"), list))
        print("     cities.html JSON-LD 合法，ItemList =", n)
    except Exception as e:
        print("!! JSON 非法:", e)


def fix_prices_yichun():
    f = "prices.html"
    h = read(f)
    o = h
    h = re.sub(r'(data-slug="yichun"\s+data-cn=")伊春(")', r'\1宜春\2', h)
    report(f, o, h, "yichun data-cn 伊春→宜春")


def main():
    fix_jianyang()
    fix_luzhi()
    fix_cities_jsonld()
    fix_prices_yichun()
    print("done (dry=%s)" % DRY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上核验本次修复（2026-11-17 数据 bug 修复 + 上一轮城市卡修复）。

用法： python3 tools/cw_live_datacheck.py
"""
import json
import re
import urllib.request

BASE = "https://www.chinawheely.com"


def get(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.status, r.read().decode("utf-8", "replace")


def main():
    ok = True

    st, h = get("/index.html")
    print("index.html", st)
    m = re.search(r'city-card" href="jian\.html".*?city-card-name">([^<]*)</span>\s*'
                  r'<span class="city-card-name-cn">([^<]*)</span>', h, re.S)
    print("  jian 卡:", m.groups() if m else "未找到")
    if not m or m.group(2) != "简阳":
        ok = False
    m2 = re.search(r'city-card" href="luzhi\.html".*?city-card-name">([^<]*)</span>', h, re.S)
    print("  luzhi 卡:", m2.group(1) if m2 else "未找到")
    if not m2 or m2.group(1).strip() != "Luzhi":
        ok = False
    n = len(re.findall(r'class="city-card" href="', h))
    print("  卡片总数:", n)

    st, h = get("/cities.html")
    print("cities.html", st)
    mm = re.search(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', h, re.S | re.I)
    d = json.loads(mm.group(1).strip())
    for g in d.get("@graph", []):
        il = g.get("itemListElement")
        if isinstance(il, list) and il and "url" in il[0]:
            names = {i["url"].rsplit("/", 1)[-1]: i["name"] for i in il}
            print("  ItemList:", len(il))
            for s in ("jian.html", "yichun.html", "yuzhou.html", "luzhi.html"):
                print("   ", s, names.get(s))
            for s in ("bitu.html", "karakax.html", "qiqihar.html", "yuxian.html"):
                if s in names:
                    print("   !! 残留", s)
                    ok = False
            if names.get("jian.html") != "简阳" or names.get("yichun.html") != "宜春":
                ok = False

    st, h = get("/prices.html")
    print("prices.html", st)
    m = re.search(r'data-slug="yichun"\s+data-cn="([^"]*)"', h)
    print("  yichun data-cn:", m.group(1) if m else "未找到")
    if not m or m.group(1) != "宜春":
        ok = False
    m = re.search(r'data-slug="jian"\s+data-cn="([^"]*)"', h)
    print("  jian data-cn:", m.group(1) if m else "未找到")
    if not m or m.group(1) != "简阳":
        ok = False

    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

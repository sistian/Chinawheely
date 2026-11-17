#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""算清「333 城市」的真相，并给出达到真 333 的补齐清单。

中国地级行政区划官方口径 = 333
  = 293 地级市 + 30 自治州 + 7 地区 + 3 盟
（直辖市 4 个算省级，不计入）

本脚本：
  1) 从 pca-code.json 还原全国地级区划清单（剔除「市辖区/县/县级市」等伪地级项）
  2) 统计站点首页 333 张卡覆盖了哪些、缺哪些
  3) 输出补齐清单
"""
import json
import os
import re
import urllib.request
from collections import defaultdict

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREF = ("https://raw.githubusercontent.com/modood/Administrative-divisions-of-China"
        "/master/dist/pca-code.json")

# 省级直辖市（其 children 是「市辖区」，不是地级）
MUNICIPAL = {"北京市", "上海市", "天津市", "重庆市"}
# 伪地级项
FAKE = {"市辖区", "县", "县级市", "待完善", "省直辖县级行政区划", "直辖县级行政区划"}


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def meta(slug):
    f = os.path.join(SITE, slug + ".html")
    if not os.path.exists(f):
        return {}
    h = open(f, encoding="utf-8", errors="replace").read()
    def g(p):
        m = re.search(p, h, re.S)
        return m.group(1) if m else ""
    return {"robots": g(r'<meta name="robots" content="([^"]*)"'),
            "canon": g(r'canonical" href="([^"]*)"').split("/")[-1].replace(".html", "")}


def main():
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    cards = re.findall(
        r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
        r'\s*<span class="city-card-name-cn">([^<]+)</span>', h[gi:ge], re.S)

    data = fetch(PREF)
    prefecture = {}
    for prov in data:
        pname = prov["name"]
        if pname in MUNICIPAL:
            continue
        for c in prov.get("children", []):
            if c["name"] in FAKE:
                continue
            prefecture[c["name"]] = pname

    print("全国地级区划（不含 4 直辖市）: %d" % len(prefecture))
    kinds = defaultdict(int)
    for n in prefecture:
        if n.endswith("市"): kinds["市"] += 1
        elif n.endswith("自治州"): kinds["自治州"] += 1
        elif n.endswith("地区"): kinds["地区"] += 1
        elif n.endswith("盟"): kinds["盟"] += 1
        else: kinds["其他:" + n] += 1
    print("  ", dict(kinds))

    # 站点卡片 → 中文名（去「市/地区/自治州/盟」后缀做匹配）
    def short(n):
        return re.sub(r"(市|地区|自治州|盟)$", "", n)

    site = []
    for slug, en, cn in cards:
        m = meta(slug)
        alias = ("noindex" in m.get("robots", "")
                 and m.get("canon") not in ("", slug))
        site.append({"slug": slug, "en": en, "cn": cn.strip(),
                     "alias": alias, "canon": m.get("canon", "")})

    site_short = {}
    for s in site:
        site_short.setdefault(s["cn"], []).append(s)

    covered = []
    missing = []
    for n, prov in prefecture.items():
        b = short(n)
        hit = None
        for cn, lst in site_short.items():
            if cn == b or cn == n or short(cn) == b:
                hit = lst
                break
        if hit:
            covered.append((n, prov, hit))
        else:
            missing.append((n, prov))

    print("\n站点覆盖地级区划: %d / %d" % (len(covered), len(prefecture)))
    print("未覆盖 %d 个：" % len(missing))
    for n, p in sorted(missing):
        print("   %-26s %s" % (n, p))

    # 站点里指向未覆盖城市 / 是别名桩的卡
    print("\n=== 站点卡片中「不指向任何已覆盖地级区划」的卡 ===")
    covered_cn = set()
    for n, prov, hit in covered:
        for s in hit:
            covered_cn.add(s["cn"])
    orphan = [s for s in site if s["cn"] not in covered_cn]
    for s in orphan:
        print("   %-11s EN=%-11s 卡中文=%-8s alias=%s canon=%s"
              % (s["slug"], s["en"], s["cn"], s["alias"], s["canon"]))

    print("\n=== 汇总 ===")
    print("  首页卡片总数        : %d" % len(site))
    print("  别名桩(noindex)     : %d" % sum(1 for s in site if s["alias"]))
    print("  指向未覆盖区划的卡  : %d" % len(orphan))
    print("  实际不同的地级区划  : %d" % len(covered))
    print("  全国地级区划        : %d" % len(prefecture))
    print("  → 补齐缺口 %d 个即可让卡片数与真实覆盖数一致" % len(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

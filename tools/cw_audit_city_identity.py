#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精确列出站点缺失的「地级市」（不含地区/自治州/盟），
并判定首页网格里的重复中文名各属于什么性质。

性质分三类：
  A 真实同名不同省（yulin_sx vs yulin 等）—— 合理，保留
  B 别名桩（noindex + canonical 指向别页）—— 不该进网格
  C 卡片中文名写错（页面正文是另一座城）—— 必须修
"""
import json
import os
import re
import urllib.request
from collections import defaultdict

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREF = ("https://raw.githubusercontent.com/modood/Administrative-divisions-of-China"
        "/master/dist/pca-code.json")


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def page(slug):
    f = os.path.join(SITE, slug + ".html")
    if not os.path.exists(f):
        return {}
    h = open(f, encoding="utf-8", errors="replace").read()
    def g(p):
        m = re.search(p, h, re.S)
        return m.group(1) if m else ""
    h1 = clean(g(r"<h1[^>]*>(.*?)</h1>"))
    m = re.search(r"([一-鿿]{2,8})", h1)
    return {"robots": g(r'<meta name="robots" content="([^"]*)"'),
            "canon": g(r'canonical" href="([^"]*)"').split("/")[-1].replace(".html", ""),
            "h1_cn": m.group(1) if m else "",
            "title": clean(g(r"<title>(.*?)</title>"))[:70]}


def main():
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    cards = re.findall(
        r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
        r'\s*<span class="city-card-name-cn">([^<]+)</span>', h[gi:ge], re.S)

    by_cn = defaultdict(list)
    for slug, en, cn in cards:
        by_cn[cn].append((slug, en))

    print("=== 首页网格中文名重复分组（含性质判定）===")
    for cn, v in sorted(by_cn.items()):
        if len(v) < 2:
            continue
        print(f"\n  【{cn}】")
        for slug, en in v:
            m = page(slug)
            kind = []
            if "noindex" in m.get("robots", "") and m.get("canon") not in ("", slug):
                kind.append("B-别名桩(canonical→%s)" % m["canon"])
            if m.get("h1_cn") and m["h1_cn"] != cn:
                kind.append("C-卡片名错(页面是 %s)" % m["h1_cn"])
            if not kind:
                kind.append("A-真实同名不同省")
            print("     %-11s EN=%-11s %-16s %s" % (slug, en, m.get("title", "")[:16], " / ".join(kind)))

    print("\n=== 站点缺失的地级市（排除地区/自治州/盟）===")
    data = fetch(PREF)
    site_cn = set(cn.strip() for _s, _e, cn in cards)
    # 去后缀得到短名集合（自治州/地区/盟 也算覆盖）
    short = set()
    for cn in site_cn:
        short.add(cn)
        short.add(re.sub(r"(市|地区|自治州|盟)$", "", cn))
    missing = []
    for prov in data:
        for c in prov.get("children", []):
            n = c["name"]
            if not n.endswith("市"):
                continue
            b = n[:-1]
            if b in short or n in site_cn:
                continue
            missing.append((b, prov["name"]))
    print("  缺失 %d 个：" % len(missing))
    for b, p in sorted(missing):
        print("     %-10s %s" % (b, p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

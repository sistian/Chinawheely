#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终决策表：首页 333 张卡里，哪些是「重复占位」/「名字写错」，以及
可用来补位的真实缺失城市（源图有照片）。

输出三张表：
  T1 重复中文名组 + 每张卡的真实身份
  T2 别名桩（noindex+canonical→别页）
  T3 源图有照片、但网格里没有的城市名（可补位）
"""
import os
import re
from collections import defaultdict

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.expanduser("~"), "Desktop", "中国城市图片")

# slug -> 真实中文名（依据页面正文自述 + 行政区划常识）
CN_NAME = {
    "yuzhou": "禹州",      # 河南禹州（许昌代管）
    "bozhou": "亳州",      # 安徽亳州
    "karakax": "和田",     # 喀拉喀什 → 和田
    "kashgar": "喀什",     # 新疆喀什
    "hoting": "和田",      # 新疆和田
    "bitu": "毕节",        # 贵州毕节（异译）
    "bijie": "毕节",
    "yuxian": "郁县",      # 云南普洱郁县（历史名）
    "yuxi": "玉溪",        # 云南玉溪
    "qiqihar": "齐齐哈尔",
    "qiqihaer": "齐齐哈尔",
    "jian": "建阳",        # 福建建阳
}


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
    d = {s: (e, c.strip()) for s, e, c in cards}

    by_cn = defaultdict(list)
    for s, (e, c) in d.items():
        by_cn[c].append(s)

    print("=== T1 中文名重复组 ===")
    for cn, slugs in sorted(by_cn.items()):
        if len(slugs) < 2:
            continue
        print()
        print("  卡片显示「%s」:" % cn)
        for s in slugs:
            m = meta(s)
            alias = ("noindex" in m.get("robots", "")
                     and m.get("canon") not in ("", s))
            fix = CN_NAME.get(s)
            if alias:
                note = "→ 别名桩，canonical=%s，应从网格移除" % m["canon"]
            elif fix and fix != cn:
                note = "→ 卡片中文名应为「%s」" % fix
            else:
                note = "→ 名字正确"
            print("     %-11s EN=%-11s %s" % (s, d[s][0], note))

    print()
    print("=== T2 别名桩（noindex + canonical 指向别页）===")
    for s, (e, c) in sorted(d.items()):
        m = meta(s)
        if "noindex" in m.get("robots", "") and m.get("canon") not in ("", s):
            print("   %-11s 卡CN=%-8s canonical→%s" % (s, c, m["canon"]))

    print()
    print("=== T3 源图有照片但网格里没有的城市名 ===")
    srcs = os.listdir(SRC) if os.path.isdir(SRC) else []
    src_cn = defaultdict(int)
    for f in srcs:
        m = re.match(r"^(.+?)[A-Za-z]+[-_]?\d*\.jpg$", f)
        if m:
            src_cn[m.group(1)] += 1
    grid_cn = set(c for _e, c in d.values())
    for cn, n in sorted(src_cn.items()):
        if cn not in grid_cn:
            print("   %-10s %2d 张" % (cn, n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

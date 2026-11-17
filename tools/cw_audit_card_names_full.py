#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量扫描：首页 333 张卡片的中文名 / 英文名 与其页面自身内容是否一致。

对每个 slug 提取三处名称：
  card   —— 卡片上显示的中文名 + 英文名
  h1     —— 页面 <h1> 里的中文名
  body   —— 正文首次出现的「英文名 (中文名)」模式

标出：
  [A] 别名桩      页面 noindex 且 canonical 指向别的 slug  → 不该占卡片位
  [B] 中文名冲突  卡片中文名与 h1 中文名不同
  [C] 正文串页    卡片英文名在正文中完全不出现
  [D] 中文名重复  同一中文名出现在多张卡
"""
import os
import re
from collections import defaultdict

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    b = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
    b = re.sub(r"<style.*?</style>", " ", b, flags=re.S)
    body = clean(re.sub(r"<[^>]+>", " ", b))
    return {
        "robots": g(r'<meta name="robots" content="([^"]*)"'),
        "canon": g(r'canonical" href="([^"]*)"').split("/")[-1].replace(".html", ""),
        "h1": h1[:70],
        "h1_cn": m.group(1) if m else "",
        "body": body,
        "title": clean(g(r"<title>(.*?)</title>"))[:70],
    }


def main():
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    cards = re.findall(
        r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
        r'\s*<span class="city-card-name-cn">([^<]+)</span>', h[gi:ge], re.S)

    info = {}
    for slug, en, cn in cards:
        info[slug] = {"en": en, "cn": cn.strip(), **page(slug)}

    by_cn = defaultdict(list)
    for slug, d in info.items():
        by_cn[d["cn"]].append(slug)

    print("=== A) 别名桩（noindex + canonical 指向别页）→ 不该占卡片位 ===")
    n = 0
    for slug, d in info.items():
        if "noindex" in d.get("robots", "") and d.get("canon") not in ("", slug):
            n += 1
            print("   %-11s 卡EN=%-11s 卡CN=%-6s canonical→%s" % (slug, d["en"], d["cn"], d["canon"]))
    print("   合计 %d" % n)

    print("\n=== B) 卡片中文名 与 页面 h1 中文名 不一致 ===")
    n = 0
    for slug, d in info.items():
        if d.get("h1_cn") and d["h1_cn"] != d["cn"]:
            n += 1
            print("   %-11s 卡CN=%-8s h1CN=%-8s h1=%s" % (slug, d["cn"], d["h1_cn"], d["h1"][:50]))
    print("   合计 %d" % n)

    print("\n=== C) 卡片英文名在正文里完全不出现 ===")
    n = 0
    for slug, d in info.items():
        if d["en"] and d["en"] not in d.get("body", ""):
            n += 1
            print("   %-11s 卡EN=%-12s 卡CN=%-8s title=%s" % (slug, d["en"], d["cn"], d["title"]))
    print("   合计 %d" % n)

    print("\n=== D) 中文名重复的卡片 ===")
    n = 0
    for cn, slugs in sorted(by_cn.items()):
        if len(slugs) > 1:
            n += 1
            print("   %-8s <- %s" % (cn, [(s, info[s]["en"]) for s in slugs]))
    print("   合计 %d 组" % n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

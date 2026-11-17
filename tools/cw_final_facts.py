#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补齐最后几个事实：
  1) 网格里 fuzhou/suzhou/liangshan/tacheng 等的 CN 名（确认 T3 里 福州/苏州 为何被判"缺失"）
  2) index.html 里 "333" 的用法（是卡片数还是覆盖声明）
  3) 站内地级市页的真实数量（与 333 覆盖声明对照）
  4) 可补位候选：吉安/哈密/梁山 等是否已有页面
"""
import os
import re
from collections import defaultdict

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    d = {}
    for s, e, c in re.findall(
            r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
            r'\s*<span class="city-card-name-cn">([^<]+)</span>', h[gi:ge], re.S):
        d[s] = (e, c.strip())

    print("=== 1) 关键 slug 的卡片名 ===")
    for s in ["fuzhou", "fuzhou_jx", "suzhou", "suzhou_ah", "liangshan",
              "tacheng", "yili", "aksu", "gannan", "dali", "honghe", "linxia",
              "yanbian", "changji", "xingan", "xilinhot", "alxa", "daxingan",
              "qdn", "qnan", "qxn", "dehong", "chuxiong", "nujiang", "diqing",
              "ganzi", "aba", "huangnan", "haibei", "haixi", "guoluo", "yushu",
              "bortala", "kizilsu", "bayin", "xishuangbanna", "jining", "zibo"]:
        print("   %-16s %s" % (s, d.get(s, "不在网格")))

    print("\n=== 2) index.html 中 '333' 的上下文 ===")
    for m in re.finditer(r".{60}333.{60}", h, re.S):
        t = re.sub(r"\s+", " ", m.group(0))
        if "card" in t.lower() and "grid" in t.lower():
            continue
        print("   ", t)

    print("\n=== 3) 站内地级市页数（含别名桩）===")
    n = 0
    for f in os.listdir(SITE):
        if not f.endswith(".html"):
            continue
        t = open(os.path.join(SITE, f), encoding="utf-8", errors="replace").read()
        if "Airport Transfer" in t and "ChinaWheely" in t:
            n += 1
    print("   含 'Airport Transfer' 标题的城市页:", n)

    print("\n=== 4) 候选补位城市是否已有页面 ===")
    for cand in ["jian2", "ji_an", "jian_an", "hami", "liangshan2", "huanning",
                 "nanyang", "moyu", "lufeng", "jiaxian", "ulaanbaatar",
                 "xinyang", "fuzhou2", "suzhou2"]:
        print("   %-14s %s" % (cand, "有页面" if os.path.exists(
            os.path.join(SITE, cand + ".html")) else "无"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

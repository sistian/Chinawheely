#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交叉比对：
  1) 源图目录里出现的城市名 —— 哪些还没有对应页面/卡片（可用照片但没建站的城）
  2) 已有页面但不在首页网格的 slug
输出「可用照片 + 已有页面」的可补位城市清单。
"""
import os
import re
from collections import defaultdict

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.expanduser("~"), "Desktop", "中国城市图片")


def main():
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    cards = re.findall(
        r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
        r'\s*<span class="city-card-name-cn">([^<]+)</span>', h[gi:ge], re.S)
    grid = {s: (e, c) for s, e, c in cards}
    grid_cn = set(c for _e, c in grid.values())

    # 站点里所有 html 页面
    pages = set(f[:-5] for f in os.listdir(SITE) if f.endswith(".html"))

    # 源图目录：按「中文名」聚合
    srcs = os.listdir(SRC) if os.path.isdir(SRC) else []
    src_by_cn = defaultdict(list)
    for f in srcs:
        m = re.match(r"^(.+?)[A-Za-z]+[-_]?\d*\.jpg$", f)
        if m:
            src_by_cn[m.group(1)].append(f)

    print("源图目录城市条目: %d" % len(src_by_cn))
    print("首页网格城市卡  : %d" % len(grid))

    # 源图有、但网格里没有的
    missing_from_grid = []
    for cn, files in sorted(src_by_cn.items()):
        if cn in grid_cn:
            continue
        # 该中文名是否已有页面（slug 未知，按拼音猜）
        missing_from_grid.append((cn, len(files), files[:2]))
    print("\n=== 源图有照片、但首页网格没有该城市名: %d ===" % len(missing_from_grid))
    for cn, n, ex in missing_from_grid:
        print("   %-10s %2d 张  %s" % (cn, n, ex))

    # 网格里的 slug 在页面上都存在吗
    print("\n=== 网格 slug 缺页面 ===")
    miss = [s for s in grid if s not in pages]
    print("   ", miss if miss else "无")

    # 已有页面且不在网格的城市页（排除主题页/工具页）
    theme = ("best-time", "tea-culture", "day-trips", "photo-spots",
             "food-shopping", "detailed", "airport-transfer-to")
    notin = []
    for s in sorted(pages):
        if s in grid:
            continue
        if any(t in s for t in theme):
            continue
        if s in ("index", "cities", "prices", "booking", "contact", "help",
                 "about", "cookies", "services", "partners", "careers", "admin",
                 "cancellation", "manage-order", "thank-you", "404",
                 "sitemap", "seo-swot-analysis", "batch_download",
                 "image_downloader"):
            continue
        notin.append(s)
    print("\n=== 有页面但不在网格（%d 个）===" % len(notin))
    print("   ", notin)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""权威核对：全国 342 个地级行政区划 vs 站点实际页面（按 slug 存在性）。

用法： python3 tools/cw_coverage_truth.py
"""
import json
import os
import re
import urllib.request

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREF = "https://raw.githubusercontent.com/modood/Administrative-divisions-of-China/master/dist/pca-code.json"

# 地级名称 → 站点 slug 候选（人工映射，权威清单 pca-code.json 的中文名 → 站点 slug）
SLUG = {
    "临夏回族": "linxia", "伊犁哈萨克": "yili", "克孜勒苏柯尔克孜": "kizilsu",
    "兴安盟": "hulunbuir", "凉山彝族": "liangshan", "博尔塔拉蒙古": "bortala",
    "吉安": "jian", "塔城": "tacheng", "大兴安岭": "daxingan",
    "大理白族": "dali", "巴音郭楞蒙古": "bayingolin", "延边朝鲜族": "yanbian",
    "德宏傣族景颇族": "dehong", "怒江傈僳族": "nujiang", "恩施土家族苗族": "enshi",
    "文山壮族苗族": "wenshan", "昌吉回族": "changji", "果洛藏族": "guoluo",
    "楚雄彝族": "chuxiong", "海北藏族": "haibei", "海南藏族": "hainan",
    "海西蒙古族藏族": "haixi", "湘西土家族苗族": "xiangxi", "玉树藏族": "yushu",
    "甘南藏族": "gannan", "甘孜藏族": "ganzi", "红河哈尼族彝族": "honghe",
    "西双版纳傣族": "xishuangbanna", "迪庆藏族": "diqing", "锡林郭勒盟": "xilingol",
    "阿克苏": "aksu", "阿勒泰": "altay", "阿坝藏族羌族": "aba",
    "阿拉善盟": "alxa", "阿里": "ali", "黄南藏族": "huangnan",
    "黔东南苗族侗族": "qiandongnan", "黔南布依族苗族": "qiannan",
    "黔西南布依族苗族": "qianxinan",
}
JUNK = {"县", "辖区", "省直辖县级行政区划", "自治区直辖县级行政区划", "市辖区", "待完善"}


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def index_cards():
    """从 index.html 网格取 slug→中文名（权威口径）。"""
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    seg = h[gi:ge]
    pairs = re.findall(
        r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
        r'\s*<span class="city-card-name-cn">([^<]+)</span>', seg, re.S)
    return {s: cn.strip() for s, en, cn in pairs}


def main():
    data = fetch(PREF)
    prefecture = {}
    for prov in data:
        pname = prov["name"].replace("省", "").replace("市", "").replace("自治区", "")
        for c in prov.get("children", []):
            nm = c["name"]
            if nm in JUNK:
                continue
            base = nm.replace("市", "").replace("地区", "").replace("自治州", "").replace("盟", "")
            prefecture[base] = (nm, pname)

    cards = index_cards()
    card_cn = set(v.replace("市", "").replace("地区", "").replace("自治州", "").replace("盟", "")
                   for v in cards.values())

    have, missing = [], []
    for base, (nm, pname) in sorted(prefecture.items()):
        hit = base in card_cn
        slug = SLUG.get(nm) or SLUG.get(base)
        page = bool(slug and os.path.exists(os.path.join(SITE, slug + ".html")))
        (have if (hit or page) else missing).append((base, nm, pname, slug, hit, page))

    print("全国地级区划(去重复/无效):", len(prefecture))
    print("站点覆盖:", len(have), " 缺失:", len(missing))
    print("\n== 缺失（既无卡片也无页面）==")
    for base, nm, pname, slug, hit, page in missing:
        print("  %-14s %-14s slug=%s" % (base, pname, slug))
    print("\n== 有页面但无卡片（仅 slug 命中）==")
    for base, nm, pname, slug, hit, page in have:
        if page and not hit:
            print("  %-14s %-14s slug=%s" % (base, pname, slug))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

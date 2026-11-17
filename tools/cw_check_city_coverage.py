#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对站点覆盖的「地级市/地区」与全国权威名单的差距。

数据源：modood/Administrative-divisions-of-China 的 pcas-code.json
        （省 → 市辖区 → 县级）
        + pca-code.json（省 → 地级）

用法： python3 tools/cw_check_city_coverage.py
"""
import json
import os
import re
import urllib.request

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREF = "https://raw.githubusercontent.com/modood/Administrative-divisions-of-China/master/dist/pca-code.json"

NON_CITY = {"市辖区", "县", "县级市", "自治区", "省直辖县级行政区划", "待完善", "直辖县级行政区划"}


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def load_site_cities():
    """从 prices.html 取站点自认的城市清单（权威口径）。"""
    p = os.path.join(SITE, "prices.html")
    h = open(p, encoding="utf-8").read()
    slugs = set(re.findall(r'href="([a-z_0-9]+)\.html"', h))
    drop = {"index", "cities", "prices", "booking", "contact", "help", "about",
            "cookies", "services", "partners", "careers", "admin", "cancellation",
            "manage-order", "thank-you", "404"}
    return slugs - drop


def main():
    data = fetch(PREF)
    # 地级名单：省 -> children
    prefectures = []
    for prov in data:
        pname = prov["name"].replace("省", "").replace("市", "").replace("自治区", "")
        for c in prov.get("children", []):
            prefectures.append((c["name"], pname))
    print("全国地级行政区划（省/自治区/直辖市 + 地级市/地区/自治州）:", len(prefectures))

    site = load_site_cities()
    print("站点城市清单(prices.html):", len(site))

    # 站点中文名：直接取首页卡片上的中文名（权威口径，与 prices.html 同源）
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    pairs = re.findall(
        r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
        r'\s*<span class="city-card-name-cn">([^<]+)</span>', h[gi:ge], re.S)
    cn = {slug: cnname for slug, en, cnname in pairs}
    site_cn = set(cnname.strip().replace("市", "").replace("地区", "")
                   .replace("自治州", "").replace("盟", "") for cnname in cn.values())
    print("站点解析出的中文名:", len(site_cn), "(卡片数 %d)" % len(cn))

    have = set()
    for name, _p in prefectures:
        base = name.replace("市", "").replace("地区", "").replace("自治州", "")
        if base in site_cn:
            have.add(base)
    missing = sorted(set(n.replace("市", "").replace("地区", "").replace("自治州", "")
                          for n, _ in prefectures) - site_cn)
    print("站点未覆盖的地级区划 (%d):" % len(missing))
    for m in missing:
        print("   ", m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

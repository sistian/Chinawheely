#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""民族自治州/地区/盟 用「去民族后缀」的短名匹配后，
统计站点真正缺失的地级「市」，并检查这些市在源图目录里有没有照片。
"""
import json
import os
import re
import urllib.request
from collections import defaultdict

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.expanduser("~"), "Desktop", "中国城市图片")
PREF = ("https://raw.githubusercontent.com/modood/Administrative-divisions-of-China"
        "/master/dist/pca-code.json")
MUNICIPAL = {"北京市", "上海市", "天津市", "重庆市"}
FAKE = {"市辖区", "县", "县级市", "待完善", "省直辖县级行政区划", "直辖县级行政区划"}
ETHNIC = r"(回族|藏族|维吾尔|哈萨克|蒙古|柯尔克孜|朝鲜族|白族|傣族|景颇|土家族|苗族|布依族|侗族|傈僳族|彝族|羌族|壮族|傣|拉祜族|佤族)"


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    cards = re.findall(
        r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
        r'\s*<span class="city-card-name-cn">([^<]+)</span>', h[gi:ge], re.S)
    site_cn = set(cn.strip() for _s, _e, cn in cards)

    data = fetch(PREF)
    prefecture = {}
    for prov in data:
        if prov["name"] in MUNICIPAL:
            continue
        for c in prov.get("children", []):
            if c["name"] in FAKE:
                continue
            prefecture[c["name"]] = prov["name"]

    def keys(n):
        """一个地级名可接受的所有站点写法。"""
        out = {n}
        b = re.sub(r"(市|地区|自治州|盟)$", "", n)
        out.add(b)
        out.add(re.sub(ETHNIC + r"?(自治州)?$", "", b))
        out.add(re.sub(ETHNIC, "", b))
        return {x for x in out if x}

    site_keys = set()
    for cn in site_cn:
        site_keys |= keys(cn)

    missing = [(n, p) for n, p in prefecture.items()
               if not (keys(n) & site_keys)]
    print("=== 真正缺失的地级区划：%d / %d ===" % (len(missing), len(prefecture)))
    for n, p in sorted(missing):
        print("   %-24s %s" % (n, p))

    # 源图目录里有没有对应照片
    if os.path.isdir(SRC):
        srcs = os.listdir(SRC)
        print("\n=== 缺失项在源图目录是否有照片 ===")
        for n, p in sorted(missing):
            base = re.sub(r"(市|地区|自治州|盟)$", "", n)
            hits = [s for s in srcs if s.startswith(base[:2]) and s.endswith(".jpg")]
            print("   %-24s %s" % (n, hits[:4] if hits else "无"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

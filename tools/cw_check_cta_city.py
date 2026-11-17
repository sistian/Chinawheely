#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""门禁：城市页的 booking.html?city= 参数必须解析到本页自己的城市。

booking.js 的 resolveCityParam() 会把参数归一化（去空格/连字符/撇号）后，
在 pricing.json 的 slug/en/cn 里找第一个匹配。同名城市（福州/抚州、苏州/宿州、
台州/泰州、玉林/榆林、伊春/宜春、简阳/建阳）用英文名做参数会命中**另一个省**的城市，
导致订车表单预选错城市。

用法：python3 tools/cw_check_cta_city.py [站点根目录]
退出码 0 = 通过；1 = 存在错配
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# 同城别名页：参数指向的是同一座城市的正牌页，允许
ALIAS_OK = {("bitu", "bijie"), ("qiqihar", "qiqihaer")}

# 主题页（母城的子页），参数指向母城是正确的
THEME = re.compile(r"-(best-time|day-trips|food-shopping|photo-spots|tea-culture)$")
NON_CITY = {"index", "booking", "contact", "prices", "manage-order", "admin", "about", "terms",
            "privacy", "help", "careers", "services", "cancellation", "cookies", "partners",
            "404", "seo-swot-analysis", "cities", "thank-you"}


def norm(s):
    return re.sub(r"[\s\-_'’.]+", "", str(s or "").lower())


def main():
    with open(os.path.join(ROOT, "pricing", "pricing.json"), encoding="utf-8") as fh:
        cities = json.load(fh).get("cities", {})

    idx = {}
    for slug, c in cities.items():
        if not isinstance(c, dict):
            continue
        for k in (slug, c.get("en"), c.get("cn")):
            if k:
                idx.setdefault(norm(k), slug)

    bad = []
    for f in sorted(os.listdir(ROOT)):
        if not f.endswith(".html"):
            continue
        s = f[:-5]
        if s in NON_CITY or THEME.search(s):
            continue
        h = open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read()
        for p in sorted(set(re.findall(r'href="[^"]*booking\.html\?city=([^"&]+)', h))):
            hit = idx.get(norm(p.replace("&amp;", "&").split("&")[0]))
            if hit and hit != s and (s, hit) not in ALIAS_OK:
                bad.append((f, p, hit))

    print("CTA 城市预填错配: %d" % len(bad))
    for f, p, hit in bad:
        print("  %-18s ?city=%-22s → 解析到 %s" % (f, p, hit))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

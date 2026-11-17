#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精确核对三组同名城市的真实身份 + 找出真正缺失的地级市。

1) yuzhou / karakax / yuxian 的页面正文自述身份（省 + 是否与 hoting 重复）
2) 自治州/地区/盟 用短名匹配后，站点仍缺失的地级区划
"""
import json
import os
import re
import urllib.request

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREF = ("https://raw.githubusercontent.com/modood/Administrative-divisions-of-China"
        "/master/dist/pca-code.json")


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def body_text(slug):
    f = os.path.join(SITE, slug + ".html")
    if not os.path.exists(f):
        return ""
    h = open(f, encoding="utf-8", errors="replace").read()
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()


def main():
    print("=== 1) 同名城市的正文自述 ===")
    for slug in ["yuzhou", "bozhou", "karakax", "kashgar", "hoting",
                 "yuxi", "yuxian", "jian", "bitu", "bijie"]:
        t = body_text(slug)
        if not t:
            print(f"  {slug}: 无页面")
            continue
        provs = sorted(set(re.findall(
            r"(Anhui|Henan|Xinjiang|Yunnan|Guizhou|Jiangxi|Heilongjiang|Fujian|"
            r"Jiangsu|Zhejiang|Shandong|Henan|Hebei|Hubei|Hunan|Anhui|Guangdong|"
            r"Gansu|Ningxia|Shaanxi|Shanxi|Inner Mongolia|Tibet)", t)))
        # 关键句
        keys = re.findall(r"[^.]*?(?:Yuzhou|Karakax|Kashgar|Hotan|Yuxian|Yuxi|Bijie|"
                          r"Jianyang|Ji'an)[^.]*\.", t[:3000])
        print(f"  {slug:9s} provinces={provs}")
        for k in keys[:3]:
            print("       ", k.strip()[:170])

    print("\n=== 2) 真正缺失的地级区划（自治州/地区/盟 用短名再匹配一次）===")
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    cards = re.findall(
        r'city-card" href="([a-z_0-9]+)\.html"[^>]*>.*?city-card-name">([^<]+)</span>'
        r'\s*<span class="city-card-name-cn">([^<]+)</span>', h[gi:ge], re.S)
    site_cn = set(cn.strip() for _s, _e, cn in cards)
    # 短名集合：自治州→凉山 / 地区→塔城 / 盟→兴安
    short = set()
    for cn in site_cn:
        short.add(cn)
        short.add(re.sub(r"(彝族|回族|藏族|维吾尔|哈萨克|蒙古|柯尔克孜|朝鲜族|"
                         r"白族|傣族|景颇|土家族|苗族|布依族|侗族|自治州)$", "", cn))
    data = fetch(PREF)
    prefect = {}
    for prov in data:
        for c in prov.get("children", []):
            prefect[c["name"]] = prov["name"]
    def base(n):
        b = re.sub(r"(市|地区|自治州|盟|特别行政区)$", "", n)
        b = re.sub(r"(彝族|回族|藏族|维吾尔|哈萨克|蒙古|柯尔克孜|朝鲜族|白族|"
                   r"傣族|景颇|土家族|苗族|布依族|侗族)?自治州$", "", b)
        return b
    missing = [(n, p) for n, p in prefect.items()
               if base(n) not in short and n not in site_cn]
    print("  仍未覆盖：%d 个" % len(missing))
    for n, p in sorted(missing):
        print("     %-26s %s" % (n, p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

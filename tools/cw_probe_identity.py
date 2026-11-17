#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐个核查站点里「中文名重复 / 英文名与中文名不匹配」的城市页真实身份。

对每个可疑 slug，打印：标题、H1、正文首段出现的地名、所属省线索，
用于人工判定「是别名页 / 是真错配 / 是另一座城」。
"""
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUSPECTS = ["bozhou", "yuzhou", "karakax", "kashgar", "bijie", "bitu",
            "yuxi", "yuxian", "jian", "qiqihar", "qiqihaer", "hoting"]


def main():
    for slug in SUSPECTS:
        f = os.path.join(SITE, slug + ".html")
        if not os.path.exists(f):
            print(f"\n### {slug}: 无页面")
            continue
        h = open(f, encoding="utf-8", errors="replace").read()
        title = re.search(r"<title>(.*?)</title>", h, re.S)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
        robots = re.search(r'<meta name="robots" content="([^"]*)"', h)
        canon = re.search(r'canonical" href="([^"]*)"', h)
        desc = re.search(r'<meta name="description" content="([^"]*)"', h)

        def clean(s):
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()

        body = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
        body = re.sub(r"<style.*?</style>", " ", body, flags=re.S)
        text = clean(body)
        # 正文前 400 字
        print(f"\n### {slug}")
        print("  title   :", clean(title.group(1) if title else ""))
        print("  h1      :", clean(h1.group(1) if h1 else "")[:120])
        print("  robots  :", robots.group(1) if robots else "")
        print("  canon   :", canon.group(1) if canon else "")
        print("  desc    :", clean(desc.group(1) if desc else "")[:160])
        print("  body    :", text[:300])
        # 出现的省名
        provs = [p for p in ["Anhui", "Henan", "Xinjiang", "Yunnan", "Guizhou",
                             "Jiangxi", "Heilongjiang", "Fujian", "Guangdong",
                             "Shanxi", "Shandong", "Jiangsu", "Zhejiang"]
                 if p.lower() in text.lower()]
        print("  provinces:", provs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

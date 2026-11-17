#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新 cities.html 的 JSON-LD ItemList（加新城市、重排 position、更新 numberOfItems）
幂等
"""
import json, os, re

REPO = "/Users/w/Desktop/Chinawheely 10.27"
NEW = [
    ("yili", "伊犁哈萨克自治州"), ("kizilsu", "克孜勒苏柯尔克孜自治州"), ("bortala", "博尔塔拉蒙古自治州"),
    ("tacheng", "塔城地区"), ("bayingolin", "巴音郭楞蒙古自治州"), ("changji", "昌吉回族自治州"),
    ("aksu", "阿克苏地区"), ("altay", "阿勒泰地区"), ("daxingan", "大兴安岭地区"),
    ("dehong", "德宏傣族景颇族自治州"), ("nujiang", "怒江傈僳族自治州"), ("chuxiong", "楚雄彝族自治州"),
    ("xishuangbanna", "西双版纳傣族自治州"), ("diqing", "迪庆藏族自治州"), ("enshi", "恩施土家族苗族自治州"),
    ("guoluo", "果洛藏族自治州"), ("haibei", "海北藏族自治州"), ("hainan_qh", "海南藏族自治州"),
    ("haixi", "海西蒙古族藏族自治州"), ("yushu", "玉树藏族自治州"), ("huangnan", "黄南藏族自治州"),
    ("ganzi", "甘孜藏族自治州"), ("aba", "阿坝藏族羌族自治州"), ("xilingol", "锡林郭勒盟"),
    ("alxa", "阿拉善盟"), ("ali", "阿里地区"), ("qiandongnan", "黔东南苗族侗族自治州"),
    ("qiannan", "黔南布依族苗族自治州"), ("qianxinan", "黔西南布依族苗族自治州"), ("jian_jx", "吉安市"),
]
SITE = "https://www.chinawheely.com"
p = os.path.join(REPO, "cities.html")
h = open(p, encoding="utf-8").read()

m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', h, re.S)
data = json.loads(m.group(2))

def walk(node):
    if isinstance(node, dict):
        if node.get("@type") == "ItemList":
            return [node]
        out = []
        for v in node.values():
            out += walk(v)
        return out
    if isinstance(node, list):
        out = []
        for v in node:
            out += walk(v)
        return out
    return []

il = walk(data)[0]
items = il["itemListElement"]
have = {it["url"].rsplit("/", 1)[-1].replace(".html", "") for it in items}
added = 0
for slug, cn in NEW:
    if slug in have:
        continue
    items.append({"@type": "ListItem", "position": len(items) + 1, "name": cn,
                  "url": "%s/%s.html" % (SITE, slug)})
    added += 1
for i, it in enumerate(items, 1):
    it["position"] = i
il["numberOfItems"] = len(items)
il["itemListElement"] = items

h = h[:m.start(2)] + json.dumps(data, ensure_ascii=False, indent=2) + h[m.end(2):]
open(p, "w", encoding="utf-8").write(h)
print("cities.html ItemList: 新增 %d，总数 %d" % (added, len(items)))

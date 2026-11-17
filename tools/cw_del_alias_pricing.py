#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 pricing.json 删除已别名化的 karakax / yuxian（filledFrom + 城市价格块）。"""
import json
import os

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(SITE, "pricing", "pricing.json")

d = json.load(open(P, encoding="utf-8"))
for k in ["filledFrom"]:
    if k in d:
        for s in ["karakax", "yuxian"]:
            if s in d[k]:
                del d[k][s]
                print("del %s.%s" % (k, s))
for s in ["karakax", "yuxian"]:
    if s in d.get("cities", {}):
        del d["cities"][s]
        print("del cities.%s" % s)

json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(P, "a", encoding="utf-8").write("\n")
print("cities:", len(d["cities"]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P5d —— 首页「Smart Distance Pricing」段落去伪存真

原段落写的是一套「按距离分档 $50/$65/$80/$100 + 时长档 $35/$45/$50」的定价模型，
与报价单完全不符：
  · 报价单没有距离分档，只有「固定起步价（含 35 km）+ 超时 ¥/min + 超公里 ¥/km」
  · 报价单的包车时长档是 2h/4h/6h/8h/10h，不是 4h/8h/12h
  · 报价单规定 Intercity 与接送机同价，原文却说 intercity 单列一档
改法：整段替换为与报价单一致的真实模型说明，价格示例取自真实城市。

用法: python3 tools/fix_home_distance_pricing.py
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, "pricing", "pricing.json"), encoding="utf-8"))
C = d["cities"]
R = d["meta"]["usdCnyRate"]

b = C["beijing"]
eco = b["airport"]["sedan_economy"]
tiers = b["charter"]["sedan_4"]["tiers"]

NEW = f"""
 <p class="text-small u-05a8b8ce">
 <strong>
 How our pricing actually works:
 </strong>
 Every published price is one fixed fare that already includes the airport run, the driver, tolls,
 parking and free waiting time &mdash; there is no distance banding and no hidden tier. Pick your
 vehicle, and the fare you see is the fare you pay. <br/>
 <strong>
 Airport &amp; intercity transfer (4-seat economy):
 </strong>
 From
 <strong>
 &yen;{eco['pkg']}
 </strong>
 (&asymp; ${round(eco['pkg'] / R, 2)}) in Beijing, including the first
 {eco['includedKm']} km. Beyond that we charge
 <strong>
 &yen;{eco['perMin']}/min
 </strong>
 and
 <strong>
 &yen;{eco['perKm']}/km
 </strong>
 &mdash; and <strong>intercity costs exactly the same as the airport run</strong>. <br/>
 <strong>
 Private charter by the hour (4-seat):
 </strong>
 2h from
 <strong>
 &yen;{tiers['2h_35km']['pkg']}
 </strong>
 &middot; 4h from
 <strong>
 &yen;{tiers['4h_50km']['pkg']}
 </strong>
 &middot; 6h from
 <strong>
 &yen;{tiers['6h_75km']['pkg']}
 </strong>
 &middot; 8h from
 <strong>
 &yen;{tiers['8h_100km']['pkg']}
 </strong>
 &middot; 10h from
 <strong>
 &yen;{tiers['10h_125km']['pkg']}
 </strong>
 in Beijing. Vehicle: Economy / Business / MPV / 8-11 seat van / 19-55 seat coach. <br/>
 Renminbi is our base currency and USD is shown for reference at 1 USD = &yen;{R:.2f}.
 PayPal and Alipay accepted, CNY, EUR &amp; USD welcome. </p>
 """

path = os.path.join(BASE, "index.html")
s = open(path, encoding="utf-8").read()

i = s.find("Smart Distance Pricing")
if i < 0:
    print("未找到 Smart Distance Pricing 段落")
    sys.exit(0)

# 找到该 <p ...> 的起始与结束
pstart = s.rfind("<p", 0, i)
pend = s.find("</p>", i) + len("</p>")
# 保留 p 的属性
ptag = s[pstart:s.find(">", pstart) + 1]
new_p = ptag + NEW.strip("\n") + "</p>"

s = s[:pstart] + new_p + s[pend:]
open(path, "w", encoding="utf-8").write(s)
print("首页定价模型段落已替换为报价单真实口径")

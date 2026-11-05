#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给旧模板主题页补 page-siblings 锚点（渲染器 new-template 分支需要它才能定位内容区）。
只处理指定白名单页面，不碰其他页。"""
import os
import sys

SITE = '/Users/w/Desktop/Chinawheely 10.27'
sys.path.insert(0, os.path.join(SITE, 'tools'))
import cw_footer2 as F  # noqa: E402

TARGETS = [
    'chongqing-day-trips.html',
    'chongqing-photo-spots.html',
    'beijing-tea-culture.html',
]

for f in TARGETS:
    p = os.path.join(F.ROOT, f)
    if not os.path.exists(p):
        print('缺文件', f)
        continue
    s = F.read(p)
    if 'data-siblings' in s:
        print('已有 siblings，跳过', f)
        continue
    city = F.page_city(f)
    blk = F.sibling_block(city, f)
    if not blk:
        print('无法生成 siblings 块:', f, 'city=', city)
        continue
    i = s.rfind('</body>')
    if i == -1:
        print('找不到 </body>:', f)
        continue
    F.write(p, s[:i] + blk + s[i:])
    print('已补 siblings:', f, 'city=', city)

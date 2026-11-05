#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图片瘦身：jpg/png → webp（当同目录存在更小的 webp 时）（幂等）
背景：站里同时有 images/X.jpg 和 images/X.webp，页面里引的还是大的 jpg。
     chongqing.jpg 304KB → webp 182KB；nanjing.jpg 264KB → webp 149KB；
     dalian.jpg 330KB → webp 178KB；fuzhou.jpg 459KB → ...
     这些是 hero 背景，按页加载，直接拖慢首屏。
修法：仅当 webp 存在且明显更小时才替换（引用位置：CSS url()、src=、srcset=、poster=）
"""
import os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

changed_files = 0
saved_total = 0
detail = {}

IMG = re.compile(r"""(["'(])(images/[A-Za-z0-9_\-/\.]+?)\.(jpg|jpeg|png)\1""", re.I)

def swap(m):
    global saved_total
    quote, path, ext = m.group(1), m.group(2), m.group(3)
    webp = path + '.webp'
    if not os.path.exists(webp):
        return m.group(0)
    try:
        a, b = os.path.getsize(path + '.' + ext), os.path.getsize(webp)
    except OSError:
        return m.group(0)
    if b >= a * 0.9:          # 收益太小就不折腾
        return m.group(0)
    saved_total += a - b
    detail[path + '.' + ext] = (a, b)
    return f'{quote}{webp}{quote}'


for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    h = open(f, encoding='utf-8').read()
    h2 = IMG.sub(swap, h)
    if h2 != h:
        open(f, 'w', encoding='utf-8').write(h2)
        changed_files += 1

print(f'替换 {changed_files} 个页面，累计省 {saved_total//1024} KB')
for k, (a, b) in sorted(detail.items(), key=lambda x: -(x[1][0] - x[1][1]))[:12]:
    print(f'   {k:32s} {a//1024:4d}KB → {b//1024:4d}KB  省 {(a-b)//1024}KB')

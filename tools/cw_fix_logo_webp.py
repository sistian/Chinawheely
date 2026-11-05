#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""logo.webp 重新从 logo.png（RGBA 200×200）生成（幂等）
上一版从 logo.jpg（512×512 无透明）转，导致 logo 带白底 —— 深色页脚上会出白方块。
页脚的 <picture> 是 <source srcset="images/logo.webp"> + <img src="images/logo.png">，
两者必须一致：同为 200×200 RGBA。
"""
import os
from PIL import Image

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

src = 'images/logo.png'
dst = 'images/logo.webp'
im = Image.open(src).convert('RGBA')
im.save(dst, 'WEBP', quality=90, method=4)
print(f'logo.webp: {im.size} RGBA  {os.path.getsize(dst)} bytes '
      f'(源 logo.png {os.path.getsize(src)} bytes)')

# logo.jpg 是否还被引用？
used = []
for f in sorted(os.listdir('.')):
    if f.endswith('.html'):
        h = open(f, encoding='utf-8', errors='ignore').read()
        if 'images/logo.jpg' in h:
            used.append(f)
print(f'仍引用 images/logo.jpg 的页面: {len(used)} {used[:5]}')

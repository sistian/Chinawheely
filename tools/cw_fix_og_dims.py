#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按实际图片尺寸校正 og:image:width / og:image:height（幂等）
之前全站写死 1200×630，但实际图片尺寸不一：
  - 老的城市照片 webp 是 800×533 / 800×498
  - 新生成的城市卡片是 1200×630
  - 声明尺寸和真实文件对不上时，部分抓取器会按错误尺寸裁切。
"""
import os, re
from PIL import Image

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)
SELF = 'https://www.chinawheely.com'

size_cache = {}


def size_of(url):
    if url in size_cache:
        return size_cache[url]
    rel = url.split(SELF + '/')[-1].split('?')[0]
    p = rel
    if not os.path.exists(p):
        p = os.path.join('images', os.path.basename(rel))
    try:
        with Image.open(p) as im:
            s = im.size
    except Exception:
        s = None
    size_cache[url] = s
    return s


fixed = 0
for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    h = open(f, encoding='utf-8').read()
    m = re.search(r'<meta property="og:image" content="([^"]+)"', h)
    if not m:
        continue
    url = m.group(1)
    s = size_of(url)
    if not s:
        continue
    w, ht = s
    def repl(mm):
        return (f'<meta property="og:image:width" content="{w}">'
                f'<meta property="og:image:height" content="{ht}">')
    h2, n = re.subn(r'<meta property="og:image:width" content="\d+">\s*'
                    r'<meta property="og:image:height" content="\d+">', repl, h)
    if n == 0:
        h2 = h.replace(f'<meta property="og:image" content="{url}">',
                       f'<meta property="og:image" content="{url}">\n'
                       f'<meta property="og:image:width" content="{w}">\n'
                       f'<meta property="og:image:height" content="{ht}">')
        n = 1
    if h2 != h:
        open(f, 'w', encoding='utf-8').write(h2)
        fixed += 1

print(f'校正 og:image 尺寸: {fixed} 个页面')
diffs = {}
for u, s in size_cache.items():
    diffs.setdefault(s, []).append(u.split('/')[-1])
for s, us in sorted(diffs.items(), key=lambda x: -len(x[1])):
    print(f'   {s} → {len(us)} 个文件  例: {us[:3]}')

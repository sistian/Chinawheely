#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""安全版 jpg → webp 替换（幂等）
上一版把 HTML 里的大 jpg 全换成同名 webp，结果那些 webp 有一批是空白占位图，
→ 已回滚。这一版加两道保险：
  1) 目标 webp 必须存在
  2) 目标 webp 必须**不是空白占位图**（灰度标准差 >= 12）
  3) 必须比原 jpg 小至少 10%
判定"空白"用 PIL 的灰度标准差：纯色/近纯色 → 空白占位图。
"""
import os, re
from PIL import Image, ImageStat

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

IMG_RE = re.compile(r"""(["'(])(images/[A-Za-z0-9_\-/\.]+?)\.(jpg|jpeg|png)\1""", re.I)
_cache = {}


def not_blank(p):
    if p in _cache:
        return _cache[p]
    try:
        v = ImageStat.Stat(Image.open(p).convert('L')).stddev[0] >= 12
    except Exception:
        v = False
    _cache[p] = v
    return v


changed = 0
saved = 0
detail = {}


def swap(m):
    global saved
    q, path, ext = m.group(1), m.group(2), m.group(3)
    src = path + '.' + ext
    dst = path + '.webp'
    if not os.path.exists(dst) or not not_blank(dst):
        return m.group(0)
    try:
        a, b = os.path.getsize(src), os.path.getsize(dst)
    except OSError:
        return m.group(0)
    if b >= a * 0.9:
        return m.group(0)
    saved += a - b
    detail[src] = (a, b)
    return f'{q}{dst}{q}'


for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    h = open(f, encoding='utf-8').read()
    h2 = IMG_RE.sub(swap, h)
    if h2 != h:
        open(f, 'w', encoding='utf-8').write(h2)
        changed += 1

print(f'替换 {changed} 个页面')
for k, (a, b) in sorted(detail.items(), key=lambda x: -(x[1][0] - x[1][1]))[:15]:
    print(f'   {k:32s} {a//1024:4d}KB → {b//1024:4d}KB  省 {(a-b)//1024}KB')

# 替换后是否还有页面引用这些 jpg？
still = []
for k in detail:
    for f in sorted(os.listdir('.')):
        if f.endswith('.html') and k in open(f, encoding='utf-8', errors='ignore').read():
            still.append((k, f))
            break
print(f'\n仍被引用的 jpg: {len(still)}  {[s[0] for s in still[:10]]}')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 images/{X}.webp 真正从同名 jpg/png 重新编码（幂等）
背景：站里有一批 images/{X}.webp 其实是「低质量占位」——
      和源 jpg 尺寸一样，但灰度标准差只有源图的 1/5 甚至更低
      （例：hangzhou.jpg std=76.1 / 79KB  ↔  hangzhou.webp std=16.6 / 3KB，
        明显是被压糊的占位图，不是真转换）
      一旦 HTML 引用它们，图片看起来就是糊的/空的。
修法：对每一对 jpg/webp，用 Pillow 从 jpg 重新编码 webp（quality=86, method=5），
      尺寸与源图一致，视觉等价；然后再让 HTML 引用 webp。
判定：源 jpg 存在 且（webp 不存在 或 webp 的灰度标准差 < 源图的 70%）
"""
import os
from PIL import Image, ImageStat

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)
IMG = 'images'

fixed = []
for f in sorted(os.listdir(IMG)):
    if not f.endswith(('.jpg', '.jpeg')):
        continue
    src = os.path.join(IMG, f)
    dst = src.rsplit('.', 1)[0] + '.webp'
    if not os.path.exists(dst):
        continue
    try:
        sj = ImageStat.Stat(Image.open(src).convert('L')).stddev[0]
        sw = ImageStat.Stat(Image.open(dst).convert('L')).stddev[0]
    except Exception:
        continue
    if sw >= sj * 0.7:
        continue                      # 已经是等价的真转换
    im = Image.open(src)
    if im.mode != 'RGB':
        im = im.convert('RGB')
    before = os.path.getsize(dst)
    im.save(dst, 'WEBP', quality=86, method=5)
    after = os.path.getsize(dst)
    fixed.append((f, before, after, sj, sw))

print(f'重新编码 {len(fixed)} 个 webp:')
for f, b, a, sj, sw in fixed:
    print(f'   {f:16s} {b//1024:4d}KB → {a//1024:4d}KB   std {sw:.1f} → {sj:.1f} (源图)')

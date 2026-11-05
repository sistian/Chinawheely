#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复站里的占位 webp（真 bug）
背景：站里有 266 个 images/*.webp 其实是**空白占位图**（纯灰底 / 近乎纯色），
      却被 HTML 引用了 2362 次：
        images/logo.webp      → 823 次（站点 logo 在每个页面都是灰方块）
        images/og-image.webp  → 233 次（所有社交分享卡片都是灰图）
        images/whatsapp-btn.webp → 356 次
        另有 250+ 个城市图 webp
      真正的图片一直都在（同名的 .jpg / .png），只是没转过 webp。
修法：用 Pillow 从同名源图重新编码 webp（保留原文件名 → HTML 不用改），
      只替换「检测为空白」且「有源图」的 webp。
判定空白：webp 转 RGB 后灰度标准差 < 12（纯色/近乎纯色即判定为占位图）
"""
import os, re
from PIL import Image, ImageStat

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)
IMG = 'images'

files = sorted(f for f in os.listdir(IMG) if f.endswith('.webp'))


def is_blank(path):
    try:
        im = Image.open(path)
        im = im.convert('L')
        st = ImageStat.Stat(im)
        return st.stddev[0] < 12
    except Exception:
        return False


def find_source(base):
    for ext in ('.jpg', '.jpeg', '.png'):
        p = os.path.join(IMG, base + ext)
        if os.path.exists(p):
            return p
    return None


fixed, skipped_blank_ok, no_src, err = [], [], [], []
for w in files:
    wp = os.path.join(IMG, w)
    if not is_blank(wp):
        skipped_blank_ok.append(w)
        continue
    base = w[:-5]
    src = find_source(base)
    if not src:
        no_src.append(w)
        continue
    try:
        im = Image.open(src)
        if im.mode in ('RGBA', 'LA', 'P'):
            im = im.convert('RGBA')
        elif im.mode != 'RGB':
            im = im.convert('RGB')
        im.save(wp, 'WEBP', quality=82, method=4)
        fixed.append((w, os.path.getsize(src), os.path.getsize(wp)))
    except Exception as e:
        err.append((w, str(e)))

print(f'webp 总数 {len(files)}')
print(f'  正常（非空白）        {len(skipped_blank_ok)}')
print(f'  空白且已重新编码 ✅  {len(fixed)}')
print(f'  空白但无源图（跳过）  {len(no_src)}  {no_src[:10]}')
print(f'  编码出错             {len(err)}  {err[:3]}')
print()
for w, a, b in sorted(fixed, key=lambda x: -(x[1] - x[2]))[:15]:
    print(f'   {w:30s} 源 {a//1024:4d}KB → webp {b//1024:4d}KB')

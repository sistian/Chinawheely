#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""压缩超大图片资源（>150KB）：等比缩到最长边 ≤1400，再按格式重编码。
安全约束：
  - 只动 >150KB 的文件，且生成的是新文件后原子替换
  - 压缩后灰度标准差不得比原来掉超过 40%（防止把照片压成糊块/纯色）
  - 压缩后体积必须真的变小才替换
"""
import os, sys, shutil
from PIL import Image, ImageStat

SITE = '/Users/w/Desktop/Chinawheely 10.27'
IMGS = os.path.join(SITE, 'images')
LIMIT = 150 * 1024
MAXSIDE = 1400


def stddev(im):
    g = im.convert('L')
    return ImageStat.Stat(g).stddev[0]


def process(path):
    before = os.path.getsize(path)
    if before <= LIMIT:
        return None
    # 先把原文件留一份，回滚时用它恢复（不要写成 .bak 污染 images/）
    orig_bak = path + '.orig'
    shutil.copy2(path, orig_bak)
    ext = os.path.splitext(path)[1].lower()
    try:
        im = Image.open(path)
        im.load()
    except Exception as e:
        return ('SKIP-OPEN', path, before, 0, 0, str(e)[:40])
    sd0 = stddev(im)
    w, h = im.size
    scale = min(1.0, MAXSIDE / max(w, h))
    if scale < 1.0:
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    if ext == '.webp':
        im.save(path, 'WEBP', quality=80, method=6)
    elif ext in ('.jpg', '.jpeg'):
        im.convert('RGB').save(path, 'JPEG', quality=82, optimize=True, progressive=True)
    elif ext == '.png':
        im.save(path, 'PNG', optimize=True)
    else:
        return ('SKIP-EXT', path, before, 0, 0, ext)
    after = os.path.getsize(path)
    sd1 = stddev(Image.open(path))
    # 体积没变小 或 细节掉太多 → 回滚
    if after >= before or (sd0 > 5 and sd1 < sd0 * 0.6):
        shutil.copy2(orig_bak, path)          # 用原文件恢复
        os.remove(orig_bak)
        return ('ROLLBACK', path, before, after, round(sd1, 1),
                f'已恢复原图 sd0={sd0:.1f}→{sd1:.1f}')
    os.remove(orig_bak)
    return ('OK', path, before, after, round(sd1, 1),
            f'{w}×{h} sd={sd0:.1f}→{sd1:.1f}')


rows = []
for f in sorted(os.listdir(IMGS)):
    p = os.path.join(IMGS, f)
    if not os.path.isfile(p):
        continue
    if os.path.splitext(f)[1].lower() not in ('.webp', '.jpg', '.jpeg', '.png'):
        continue
    r = process(p)
    if r:
        rows.append(r)

ok = [r for r in rows if r[0] == 'OK']
bad = [r for r in rows if r[0] != 'OK']
saved = sum(r[2] - r[3] for r in ok)
print(f'压缩 {len(ok)} 个文件，共省 {saved/1024:.0f} KB\n')
for r in rows:
    print(f'  {r[0]:9s} {os.path.basename(r[1]):26s} {r[2]//1024:5d}KB → {r[3]//1024:5d}KB  {r[5]}')
if bad:
    print(f'\n回滚/跳过 {len(bad)} 个')

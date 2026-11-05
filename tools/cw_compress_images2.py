#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二轮：把仍然 >150KB 的图片压到 150KB 以内（自适应降质量/降尺寸）
安全约束同上一轮：体积必须变小、灰度标准差不得掉超过 35%、失败自动恢复。
"""
import os, shutil
from PIL import Image, ImageStat

SITE = '/Users/w/Desktop/Chinawheely 10.27'
IMGS = os.path.join(SITE, 'images')
LIMIT = 150 * 1024


def stddev(im):
    return ImageStat.Stat(im.convert('L')).stddev[0]


rows = []
for f in sorted(os.listdir(IMGS)):
    p = os.path.join(IMGS, f)
    if not os.path.isfile(p):
        continue
    ext = os.path.splitext(f)[1].lower()
    if ext not in ('.webp', '.jpg', '.jpeg'):
        continue
    before = os.path.getsize(p)
    if before <= LIMIT:
        continue

    orig = p + '.orig'
    shutil.copy2(p, orig)
    try:
        im = Image.open(orig); im.load()
        sd0 = stddev(im)
        w, h = im.size
        best = None
        # 依次尝试：缩尺寸 + 降质量组合，取第一个达标且细节没丢的
        for scale in (1.0, 0.9, 0.82, 0.75, 0.68, 0.6):
            for q in (80, 74, 68, 62, 56):
                nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
                cand = im if scale == 1.0 else im.resize((nw, nh), Image.LANCZOS)
                tmp = p + '.tmp'
                if ext == '.webp':
                    cand.save(tmp, 'WEBP', quality=q, method=6)
                else:
                    cand.convert('RGB').save(tmp, 'JPEG', quality=q, optimize=True,
                                             progressive=True)
                sz = os.path.getsize(tmp)
                if sz <= LIMIT:
                    sd1 = stddev(Image.open(tmp))
                    if sd0 > 5 and sd1 < sd0 * 0.65:
                        os.remove(tmp)
                        continue          # 细节掉太多，换更保守的组合
                    shutil.move(tmp, p)
                    best = (scale, q, sz, sd1)
                    break
                os.remove(tmp)
            if best:
                break
        if best:
            rows.append(('OK', f, before, best[2], round(sd1, 1) if False else round(best[3], 1),
                         f'{int(w*best[0])}×{int(h*best[0])} q{best[1]}'))
        else:
            shutil.copy2(orig, p)
            rows.append(('KEEP', f, before, os.path.getsize(p), round(sd0, 1), '压不到 150KB 且细节会丢'))
    finally:
        if os.path.exists(orig):
            os.remove(orig)

for r in rows:
    print(f'  {r[0]:5s} {r[1]:26s} {r[2]//1024:4d}KB → {r[3]//1024:4d}KB  sd={r[4]}  {r[5]}')
print(f'\n处理 {len(rows)} 个，合计省 {sum(r[2]-r[3] for r in rows if r[0]=="OK")/1024:.0f} KB')

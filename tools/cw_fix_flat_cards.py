#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 images/card/ 里的「占位平图」。
背景：首页城市卡片的背景图有一批是近乎纯色的平图（灰度标准差 < 20），
      肉眼就是一块渐变色，完全没有城市照片。
做法：拿同名的真实城市照 images/<city>.webp（退化时试 .jpg/.png）
      按 640 宽裁切重编成 card 图，保存后复检标准差。
"""
import os
from PIL import Image, ImageStat

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)
CARD = 'images/card'
W = 640
MIN_SD = 20.0


def sd(im):
    return ImageStat.Stat(im.convert('L')).stddev[0]


def find_src(city):
    for ext in ('.webp', '.jpg', '.jpeg', '.png'):
        p = f'images/{city}{ext}'
        if os.path.exists(p):
            try:
                im = Image.open(p); im.load()
                if sd(im) >= MIN_SD:
                    return p, im
            except Exception:
                pass
    return None, None


rows = []
for f in sorted(os.listdir(CARD)):
    if not f.endswith('.webp'):
        continue
    city = f[:-5]
    p = os.path.join(CARD, f)
    try:
        im = Image.open(p); im.load()
    except Exception:
        continue
    s0 = sd(im)
    if s0 >= MIN_SD:
        continue
    src, sim = find_src(city)
    if sim is None:
        rows.append((city, 'NO-SRC', s0, 0, '找不到可用的真实城市照'))
        continue
    ratio = W / sim.width
    nw, nh = W, max(1, int(sim.height * ratio))
    out = sim.convert('RGB').resize((nw, nh), Image.LANCZOS)
    # 居中裁到 4:3
    target_h = int(W * 0.75)
    if out.height < target_h:
        ratio = target_h / sim.height
        out = sim.convert('RGB').resize((W, int(sim.height * ratio)), Image.LANCZOS)
    top = max(0, (out.height - target_h) // 2)
    out = out.crop((0, top, W, top + target_h))
    out.save(p, 'WEBP', quality=82, method=6)
    s1 = sd(Image.open(p))
    rows.append((city, 'FIXED', s0, s1,
                 f'{os.path.getsize(src)//1024}KB→{os.path.getsize(p)//1024}KB '
                 f'{im.size}→{out.size}'))

for r in rows:
    print(f'  {r[1]:7s} {r[0]:12s} 标准差 {r[2]:6.1f} → {r[3]:6.1f}   {r[4]}')
print(f'\n修复 {len([r for r in rows if r[1]=="FIXED"])} / 扫描出 {len(rows)} 张平图')

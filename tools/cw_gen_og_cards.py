#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给城市页生成真正的社交分享卡片（1200×630 webp）（幂等）
问题：约 250 个城市页的 og:image 指向的 images/{slug}.webp 是空白灰占位图，
      分享到微信/FB/Twitter 全是灰方块。
修法：用 Pillow 按站点品牌（深绿渐变 + logo + 城市中英文名 + 固定文案）生成卡片：
      - 有真实城市照片的城市（images/X.jpg）→ 照片铺满 + 深色渐变遮罩 + 文字
      - 没有照片的城市 → 品牌渐变底 + 文字
      文件名保持 images/{slug}.webp，HTML 不用改。
"""
import os, re, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)
IMG = 'images'
W, H = 1200, 630

FONT_BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
FONT_CJK = '/System/Library/Fonts/PingFang.ttc'
LOGO = 'images/logo.png'


def font(path, size, index=0):
    try:
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', size)


def gradient(w, h):
    """品牌绿斜向渐变"""
    g = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(g)
    c1 = (27, 77, 62)      # #1B4D3E
    c2 = (13, 92, 61)      # #0d5c3d
    c3 = (45, 106, 79)     # #2d6a4f
    for y in range(h):
        t = y / h
        for_x = c1 if t < 0.5 else c2
        to_x = c2 if t < 0.5 else c3
        f = (t * 2) if t < 0.5 else ((t - 0.5) * 2)
        col = tuple(int(for_x[i] + (to_x[i] - for_x[i]) * f) for i in range(3))
        d.line([(0, y), (w, y)], fill=col)
    return g


def cover(im, w, h):
    """等比裁剪铺满"""
    sw, sh = im.size
    sc = max(w / sw, h / sh)
    im = im.resize((max(1, int(sw * sc)), max(1, int(sh * sc))), Image.LANCZOS)
    sw, sh = im.size
    left, top = (sw - w) // 2, (sh - h) // 2
    return im.crop((left, top, left + w, top + h))


def make_card(slug, en, cn, photo=None):
    if photo and os.path.exists(photo):
        base = Image.open(photo).convert('RGB')
        base = cover(base, W, H)
        # 左侧压暗，保证文字可读
        ov = Image.new('L', (W, H), 0)
        od = ImageDraw.Draw(ov)
        for x in range(W):
            od.line([(x, 0), (x, H)], fill=int(215 * max(0, 1 - x / (W * 0.78)) ** 1.5))
        base = Image.composite(Image.new('RGB', (W, H), (12, 40, 32)), base, ov)
    else:
        base = gradient(W, H)

    d = ImageDraw.Draw(base)

    # logo
    lg = Image.open(LOGO).convert('RGBA')
    lg = lg.resize((78, 78), Image.LANCZOS)
    base.paste(lg, (64, 54), lg)
    d = ImageDraw.Draw(base)
    d.text((158, 68), 'Chinawheely', font=font(FONT_BOLD, 40), fill=(255, 255, 255))

    # 城市名
    big = font(FONT_BOLD, 86)
    # 自动缩小以适配
    while d.textlength(en, font=big) > W - 130 and big.size > 44:
        big = font(FONT_BOLD, big.size - 4)
    d.text((64, 232), en, font=big, fill=(255, 255, 255))
    y = 232 + big.size + 16

    if cn:
        cjk = font(FONT_CJK, 44, index=1)
        d.text((66, y), cn, font=cjk, fill=(190, 220, 205))
        y += 66

    d.text((64, y + 10), 'Airport Transfer & Private Car Service',
           font=font(FONT_BOLD, 40), fill=(255, 255, 255))
    d.text((64, y + 66), 'Fixed price  ·  Licensed professional drivers',
           font=font(FONT_CJK, 28, index=1), fill=(176, 208, 194))

    # 底部域名胶囊
    pill = (64, H - 96, 430, H - 40)
    d.rounded_rectangle(pill, radius=28, fill=(16, 116, 78))
    d.text((pill[0] + 34, pill[1] + 10), 'chinawheely.com',
           font=font(FONT_BOLD, 32), fill=(255, 255, 255))

    out = os.path.join(IMG, slug + '.webp')
    base.save(out, 'WEBP', quality=86, method=5)
    return out


# ---------- 城市名（从 index.html 的城市网格取，中英对照） ----------
idx = open('index.html', encoding='utf-8').read()
names = {}
for m in re.finditer(
        r'class="city-card" href="([a-zA-Z0-9_\-]+)\.html".{0,600}?'
        r'class="city-card-name">([^<]+)</span>\s*'
        r'(?:<span class="city-card-name-cn">([^<]*)</span>)?', idx, re.S):
    names[m.group(1)] = (m.group(2).strip(), (m.group(3) or '').strip())

# 空白占位 webp（且没有真实照片的）需要补名
extra = {
    'juancheng': ('Juancheng', '鄄城县'), 'karakax': ('Karakax', '喀什'),
    'yongxi': ('Yongxing', '永兴县'), 'taizhou_js': ('Taizhou, Jiangsu', '泰州市'),
    'yichun_hlj': ('Yichun, Heilongjiang', '宜春市'),
}
for k, v in extra.items():
    names.setdefault(k, v)


def is_blank(p):
    try:
        from PIL import ImageStat
        return ImageStat.Stat(Image.open(p).convert('L')).stddev[0] < 12
    except Exception:
        return False


targets = []
for w in sorted(os.listdir(IMG)):
    if not w.endswith('.webp'):
        continue
    slug = w[:-5]
    if slug in ('logo', 'og-image', 'alipay-qr', 'whatsapp-qr', 'whatsapp-btn'):
        continue
    p = os.path.join(IMG, w)
    if not is_blank(p):
        continue
    targets.append(slug)

print(f'待生成卡片: {len(targets)} 个')
made = 0
miss = []
for slug in targets:
    en, cn = names.get(slug, (slug.replace('_', ' ').title(), ''))
    photo = None
    for ext in ('.jpg', '.jpeg', '.png'):
        if os.path.exists(os.path.join(IMG, slug + ext)):
            photo = os.path.join(IMG, slug + ext)
            break
    if not en:
        miss.append(slug)
        continue
    make_card(slug, en, cn, photo)
    made += 1

print(f'已生成 {made} 张；无城市名的 {len(miss)} {miss[:10]}')

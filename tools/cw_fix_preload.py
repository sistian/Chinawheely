#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修 preload 指错图。
背景：index.html 有 8 条 <link rel="preload" href="images/<city>.webp" as="image">，
      但首页卡片实际显示的是 images/card/<city>.webp（CSS 内联背景）。
      → 这 8 张 1600px 大图在首屏白下载 462KB，还跟真正的 LCP 图抢带宽。
做法：把 preload 的 href 改成实际被渲染的那张图（属性顺序无关）。
"""
import os, re, glob

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

LINK = re.compile(r'<link\b[^>]*rel=["\']?preload["\']?[^>]*>', re.I)
HREF = re.compile(r'href=["\']([^"\']+)["\']', re.I)

changed = []
for p in sorted(glob.glob('*.html')):
    h = open(p, encoding='utf-8').read()
    orig = h

    def fix(m):
        tag = m.group(0)
        if not re.search(r'as=["\']?image["\']?', tag, re.I):
            return tag
        hm = HREF.search(tag)
        if not hm:
            return tag
        href = hm.group(1)
        if not href.startswith('images/'):
            return tag
        base = os.path.basename(href)
        body = h.replace(tag, '')
        # 本页真的引用了这张图吗？（按完整路径匹配）
        if re.search(r'(?<![A-Za-z0-9_\-/])' + re.escape(href) + r'(?![A-Za-z0-9_\-])',
                     body):
            return tag
        card = f'images/card/{base}'
        if os.path.exists(card):
            return tag.replace(f'href="{href}"', f'href="{card}"').replace(
                f"href='{href}'", f"href='{card}'")
        return tag

    h = LINK.sub(fix, h)
    if h != orig:
        open(p, 'w', encoding='utf-8').write(h)
        changed.append(p)

print(f'修正 {len(changed)} 个页面: {changed}\n')
h = open('index.html', encoding='utf-8').read()
tot = 0
for m in LINK.finditer(h):
    tag = m.group(0)
    if not re.search(r'as=["\']?image["\']?', tag, re.I):
        continue
    p = HREF.search(tag).group(1)
    sz = os.path.getsize(p) if os.path.exists(p) else 0
    tot += sz
    print(f'  {sz//1024:4d}KB  {p}')
print(f'\n首页预载图片合计 {tot/1024:.0f} KB（原 462KB）')

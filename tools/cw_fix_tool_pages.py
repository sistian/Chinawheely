#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修 batch_download.html / image_downloader.html 的头部结构
bug: <meta name="robots"> 写在了 <!DOCTYPE html> 之前 →
     浏览器会忽略后面的 DOCTYPE，页面进入 quirks mode（IE5 盒模型），
     且 charset/viewport 缺失 → 移动端不缩放、中文乱码
修法: robots meta 挪进 <head>，补 charset + viewport
"""
import os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

for f in ['batch_download.html', 'image_downloader.html']:
    if not os.path.exists(f):
        continue
    h = open(f, encoding='utf-8').read()

    # 1. 摘掉挡在 DOCTYPE 前面的 meta
    stray = re.findall(r'<meta name="robots"[^>]*>\s*', h)
    for s in stray:
        h = h.replace(s, '')

    # 2. 补 charset + viewport + robots 到 <head> 里
    m = re.search(r'<head>', h, re.I)
    if not m:
        continue
    block = ('<meta charset="utf-8">\n'
             '<meta name="viewport" content="width=device-width, initial-scale=1">\n')
    if 'name="robots"' not in h:
        block += '<meta name="robots" content="noindex, nofollow">\n'
    h = h[:m.end()] + '\n' + block + h[m.end():]

    h = re.sub(r'\n{3,}', '\n\n', h)
    open(f, 'w', encoding='utf-8').write(h)
    print(f'修复 {f}: robots meta 归位到 <head>，补 charset + viewport')

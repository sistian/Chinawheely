#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""找出 images/ 里没被任何页面引用的孤儿图片（只报告，不删）。"""
import os, re, json

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

refs = set()
for f in os.listdir('.'):
    if not (f.endswith('.html') or f.endswith('.xml') or f.endswith('.txt')
            or f.endswith('.css') or f.endswith('.js')):
        continue
    try:
        s = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in re.findall(r'images/[A-Za-z0-9_./\-]+', s):
        refs.add(m.split('?')[0])

# css/js 里也可能有相对路径
for f in os.listdir('.'):
    if f.endswith(('.css', '.js')):
        try:
            s = open(f, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        for m in re.findall(r'["\']?(?:\.\./)?images/[A-Za-z0-9_./\-]+', s):
            refs.add(m.replace("../", "").lstrip('"\''))

all_img = []
for root, dirs, files in os.walk('images'):
    for fn in files:
        p = os.path.join(root, fn).replace('\\', '/')
        all_img.append(p)

orphans = []
for p in sorted(all_img):
    if p in refs:
        continue
    # 目录索引 / 卡片目录常被整体引用，做宽松匹配
    base = os.path.basename(p)
    if any(base in r for r in refs):
        continue
    sz = os.path.getsize(p)
    orphans.append((p, sz))

total = sum(s for _, s in orphans)
print(f'images/ 共 {len(all_img)} 个文件，被引用 {len(all_img)-len(orphans)} 个')
print(f'孤儿 {len(orphans)} 个，合计 {total/1024:.0f} KB\n')
for p, s in sorted(orphans, key=lambda x: -x[1]):
    print(f'  {s//1024:5d} KB  {p}')

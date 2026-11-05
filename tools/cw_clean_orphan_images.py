#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精确找出 images/ 里没人用的文件并移到回收站（trash，不 rm）。
判定：文件名在 HTML/CSS/JS/XML/TXT/MD 里「作为独立 token」出现 0 次。
      - 排除目录整体引用（images/card/xxx.webp 这类按目录被引用的）
      - 排除 og-image.* / favicon.* / logo.* 等站点级资源
"""
import os, re, shutil, time

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)
TRASH = os.path.expanduser('~/.Trash/chinawheely-orphan-images')
os.makedirs(TRASH, exist_ok=True)

blob = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '__pycache__', 'images')]
    for fn in files:
        if fn.split('.')[-1].lower() in ('html', 'css', 'js', 'xml', 'txt', 'md', 'json'):
            try:
                blob.append(open(os.path.join(root, fn), encoding='utf-8', errors='ignore').read())
            except Exception:
                pass
ALL = '\n'.join(blob)

KEEP = ('logo', 'og-image', 'favicon', 'whatsapp', 'pay-')

cands = []
for root, dirs, files in os.walk('images'):
    for fn in files:
        p = os.path.join(root, fn).replace('\\', '/')
        cands.append(p)

removed = []
kept = []
for p in sorted(cands):
    base = os.path.basename(p)
    if any(k in base for k in KEEP):
        kept.append((p, '站点级资源')); continue
    # token 精确匹配：前面不是字母数字，名字完整出现
    pat = r'(?<![A-Za-z0-9_\-])' + re.escape(base) + r'(?![A-Za-z0-9_\-])'
    n = len(re.findall(pat, ALL))
    if n == 0:
        removed.append((p, os.path.getsize(p)))
    else:
        kept.append((p, f'引用{n}次'))

print(f'候选 {len(cands)} 个，可清理 {len(removed)} 个\n')
moved = 0
for p, sz in removed:
    dst = os.path.join(TRASH, os.path.basename(p))
    i = 1
    while os.path.exists(dst):
        dst = os.path.join(TRASH, f'{os.path.basename(p)}.{i}')
        i += 1
    shutil.move(p, dst)
    moved += 1
    print(f'  移走 {sz//1024:5d} KB  {p}')

total = sum(s for _, s in removed)
print(f'\n共移走 {moved} 个文件，{total/1024:.0f} KB → {TRASH}')
print(f'（回收站可恢复；确认无误后清空 ~/.Trash 即可）')

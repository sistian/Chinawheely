#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hreflang 归一化（幂等）
站点是全站纯英文，没有中文/其他语言版本，因此：
  - 唯一合法的 hreflang 语言是 en + x-default
  - noindex 页（33 个已合并的桩页）不需要 hreflang
  - hreflang 的 href 必须与 canonical 完全一致
  - <html lang> 必须全站 en（admin.html 是内部中文后台，保留 zh-CN）
"""
import os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

ALLOW_NO_LANG = {'admin.html'}          # 内部中文后台，noindex
stats = {'added': 0, 'removed': 0, 'fixed': 0, 'lang_fixed': 0, 'noop': 0}

for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    h = open(f, encoding='utf-8').read()
    orig = h

    # --- 1. <html lang> ---
    m = re.search(r'<html([^>]*)>', h, re.I)
    if m:
        attrs = m.group(1)
        if 'lang=' not in attrs:
            h = h[:m.start()] + f'<html lang="en"{attrs}>' + h[m.end():]
            stats['lang_fixed'] += 1
        else:
            lm = re.search(r'lang="([^"]+)"', attrs)
            if lm and lm.group(1) != 'en' and f not in ALLOW_NO_LANG:
                h = h[:m.start()] + f'<html lang="en"{attrs}>' + h[m.end():]
                stats['lang_fixed'] += 1

    # --- 2. 收集 canonical ---
    cm = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"[^>]*>', h, re.I)
    if not cm:
        cm = re.search(r'<link[^>]+href="([^"]+)"[^>]+rel="canonical"[^>]*>', h, re.I)
    canon = cm.group(1) if cm else None

    # --- 3. 摘掉所有现有 hreflang ---
    links = re.findall(r'<link[^>]+hreflang="[^"]*"[^>]*>\s*', h, re.I)
    for l in links:
        h = h.replace(l, '')
    removed = len(links)

    noindex = bool(re.search(r'<meta[^>]+name="robots"[^>]+content="[^"]*noindex', h, re.I))
    if not canon or noindex or f in ALLOW_NO_LANG:
        if removed:
            stats['removed'] += removed
        h = re.sub(r'\n{3,}', '\n\n', h)
        if h != orig:
            open(f, 'w', encoding='utf-8').write(h)
        else:
            stats['noop'] += 1
        continue

    # --- 4. 在 canonical 之后插入 en + x-default ---
    tag = (f'<link rel="alternate" hreflang="en" href="{canon}">\n'
           f'<link rel="alternate" hreflang="x-default" href="{canon}">\n')
    cm2 = re.search(r'<link[^>]+rel="canonical"[^>]*>', h, re.I)
    if not cm2:
        cm2 = re.search(r'<link[^>]+href="[^"]*"[^>]+rel="canonical"[^>]*>', h, re.I)
    pos = cm2.end()
    h = h[:pos] + '\n' + tag + h[pos:]
    stats['added'] += 2
    stats['removed'] += removed
    h = re.sub(r'\n{3,}', '\n\n', h)
    open(f, 'w', encoding='utf-8').write(h)

print('hreflang 归一化完成：')
for k, v in stats.items():
    print(f'  {k}: {v}')

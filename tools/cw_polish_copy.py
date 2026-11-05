#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文案打磨 + 模板残留扫描（幂等）
1. "professional licensed driver" → "licensed professional driver"（重复词组）
2. "licensed professional licensed driver" → "licensed professional driver"（双重 licensed）
3. 句号后小写开头（针对已知短语）
4. 扫描残留模板痕迹：inXxx / with Chinawheely X with Chinawheely / 重复词 / 空标签
"""
import os, re, sys, collections

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

FIXES = [
    (r'licensed professional licensed driver', 'licensed professional driver'),
    (r'professional licensed drivers', 'licensed professional drivers'),
    (r'professional licensed driver', 'licensed professional driver'),
    (r'\. professional licensed', '. Licensed professional'),
    (r'\. licensed professional', '. Licensed professional'),
    (r'China\. Licensed professional', 'China. Licensed professional'),
    (r'\bwith Chinawheely\s+[A-Za-z\' ]*?with Chinawheely', 'with Chinawheely'),
    (r'<div></div>', ''),
    (r'<span></span>', ''),
    (r'<p></p>', ''),
    (r'\s+<span class="u-[0-9a-f]+"></span>', ''),
]

changed = 0
for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    h = open(f, encoding='utf-8', errors='ignore').read()
    o = h
    for pat, rep in FIXES:
        h = re.sub(pat, rep, h)
    if h != o:
        open(f, 'w', encoding='utf-8').write(h)
        changed += 1
print(f'文案打磨：改写 {changed} 页')

# ---------------- 残留扫描 ----------------
print("\n=== 模板残留扫描 ===")
issues = collections.defaultdict(list)
for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    h = open(f, encoding='utf-8', errors='ignore').read()
    body = re.sub(r'<script.*?</script>', '', h, flags=re.S)

    # 1) 城市名/单词粘连：inXxx / ofXxx / toXxx
    for m in re.finditer(r'\b(?:in|of|to|for|at|with|and|from)\(?([A-Z][a-z]{2,})', body):
        w = m.group(0)
        if m.group(1) in ('The', 'This', 'Our', 'Your', 'Free', 'Fixed', 'Private',
                          'Contact', 'Book', 'More', 'Other', 'All', 'Popular', 'Travel',
                          'Flight', 'Door', 'Meet', 'Hourly', 'Airport', 'China', 'Trip',
                          'Changsha', 'Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen',
                          'Chongqing', 'Hangzhou', 'Nanjing', 'Chengdu', 'Wuhan',
                          'Harbin', 'Qingdao', 'Kunming', 'Xiamen', 'Fuzhou', 'Suzhou',
                          'Tianjin', 'Jinan', 'Zhengzhou', 'Changsha', 'Hefei', 'Nanchang',
                          'Dalian', 'Jilin', 'Yichun', 'Taizhou', 'Yulin', 'Suzhou',
                          'Fuzhou', 'Yichun', 'Taizhou', 'Yulin', 'Beijing', 'Shanghai'):
            continue
        issues['单词粘连'].append(f'{f}: {w!r}')

    # 2) 重复词（the the / is is / and and）
    for m in re.finditer(r'\b(\w{3,})\s+\1\b', body, re.I):
        issues['重复词'].append(f'{f}: {m.group(0)!r}')

    # 3) 空的 href / 未替换的模板变量
    for m in re.finditer(r'href=""|href="#"|\{\{|\}\}|\[City\]|XX+|TODO', body):
        issues['占位符残留'].append(f'{f}: {m.group(0)!r}')

    # 4) 连续大写/未替换的 slug
    for m in re.finditer(r'\b(?:slug|city_slug|attraction|name_zh)\b', body):
        issues['字段名残留'].append(f'{f}: {m.group(0)!r}')

for k, v in issues.items():
    u = sorted(set(v))
    print(f'  {k}: {len(u)} 处')
    for x in u[:5]:
        print(f'     {x}')
if not issues:
    print('  ✅ 无残留')
sys.exit(0)

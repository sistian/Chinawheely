#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精确定位待修问题清单"""
import glob, os, re, collections

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
htmls = sorted(glob.glob('*.html'))

print('① 空 href / href="#" 链接')
tot = 0
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    hits = []
    for m in re.finditer(r'<a\b[^>]*href\s*=\s*["\'](?:\s*)["\'][^>]*>', s, re.I):
        hits.append(re.sub(r'\s+', ' ', m.group(0))[:130])
    for m in re.finditer(r'<a\b[^>]*href\s*=\s*["\']#["\'][^>]*>', s, re.I):
        hits.append(re.sub(r'\s+', ' ', m.group(0))[:130])
    if hits:
        tot += len(hits)
        print('  %-22s %d 处' % (f.replace('.html', ''), len(hits)))
        for h in hits[:3]:
            print('       ' + h)
print('  合计 %d 处' % tot)

print('\n② 重复 id="best-time"（准确列表）')
dup_pages = []
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    ids = re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', s)
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    if dup:
        dup_pages.append((f, dup))
print('  %d 个页面' % len(dup_pages))
for f, d in dup_pages:
    s = open(f, encoding='utf-8', errors='ignore').read()
    lines = [i + 1 for i, l in enumerate(s.split('\n')) if 'id="best-time"' in l]
    print('   %-24s %s  行 %s' % (f.replace('.html', ''), d, lines))

print('\n③ #tea 死锚点页面')
ids_by = {}
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    ids_by[f] = set(re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', s))
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'href\s*=\s*["\']([^"\']+\.html#tea)["\']', s, re.I):
        p, _, fr = m.group(1).partition('#')
        if os.path.exists(p) and fr not in ids_by.get(p, set()):
            print('   %-22s → %s' % (f.replace('.html', ''), m.group(1)))
            break

print('\n④ h1 缺空格（城市名 + 紧跟英文）')
bad_h1 = []
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S)
    if not m:
        continue
    h = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    h = re.sub(r'\s+', ' ', h)
    if re.search(r'[a-z][A-Z]', h) or re.search(r',[A-Z][a-z]', h):
        bad_h1.append((f, h[:80]))
for f, h in bad_h1:
    print('   %-24s %s' % (f.replace('.html', ''), h))
print('  合计 %d' % len(bad_h1))

print('\n⑤ 缺 <main> 地标')
nm = [f for f in htmls if not re.search(r'<main[\s>]', open(f, encoding='utf-8', errors='ignore').read(), re.I)]
for f in nm:
    print('   ' + f)
print('  合计 %d' % len(nm))

print('\n⑥ 缺 CSP 的页面')
nc = []
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    if 'Content-Security-Policy' not in s:
        nc.append(f)
print('  %d 个: %s' % (len(nc), ', '.join(x.replace('.html', '') for x in nc[:12])))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""深挖体检发现的暗病细节"""
import glob, json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
htmls = sorted(glob.glob('*.html'))

print('=' * 88)
print('① 全部死链 / 资源失效（根路径链接在子目录部署下会 404）')
print('=' * 88)
seen = collections.Counter()
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'(?:src|href)\s*=\s*["\'](/[^"\'#?][^"\']*)["\']', s, re.I):
        u = m.group(1)
        p = u.lstrip('/').split('#')[0].split('?')[0]
        if p and not os.path.exists(p):
            # 找上下文
            i = m.start()
            ctx = re.sub(r'\s+', ' ', s[max(0, i - 90):i + len(u) + 40]).strip()
            seen[(f, u)] += 1
            print('  %-22s %-28s 次数=%d' % (f.replace('.html', ''), u, seen[(f, u)]))
            print('      ctx: ' + ctx[:170])

print('\n' + '=' * 88)
print('② 跨页死锚点')
print('=' * 88)
ids_by_file = {}
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    ids_by_file[f] = set(re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', s))
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'href\s*=\s*["\']([^"\']+\.html#[^"\']+)["\']', s, re.I):
        u = m.group(1)
        path, _, frag = u.partition('#')
        if os.path.exists(path) and frag not in ids_by_file.get(path, set()):
            i = m.start()
            ctx = re.sub(r'\s+', ' ', s[max(0, i - 80):i + len(u) + 30]).strip()
            print('  %-20s → %-34s' % (f.replace('.html', ''), u))
            print('      ctx: ' + ctx[:160])

print('\n' + '=' * 88)
print('③ 重复 id 明细')
print('=' * 88)
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    ids = re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', s)
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    if dup:
        for d in dup:
            cnt = ids.count(d)
            # 找两处所在行
            lines = [i + 1 for i, l in enumerate(s.split('\n')) if ('id="%s"' % d) in l or ("id='%s'" % d) in l]
            print('  %-20s id=%-16s 出现 %d 次，行号 %s' % (f.replace('.html', ''), d, cnt, lines[:4]))

print('\n' + '=' * 88)
print('④ 缺 alt 的 img 是什么')
print('=' * 88)
kinds = collections.Counter()
sample = {}
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'<img\b[^>]*>', s, re.I):
        if not re.search(r'\balt\s*=\s*["\'][^"\']*["\']', m, re.I):
            t = re.sub(r'\s+', ' ', m.group(0))[:120]
            key = re.search(r'src\s*=\s*["\']([^"\']+)', t)
            k = key.group(1) if key else t[:40]
            kinds[k] += 1
            sample.setdefault(k, (f, t))
for k, c in kinds.most_common(8):
    print('  [%d 页] %s' % (c, k))
    print('      例: %s' % sample[k][1][:150])

print('\n' + '=' * 88)
print('⑤ booking.html 的 _t 字段')
print('=' * 88)
s = open('booking.html', encoding='utf-8').read()
for m in re.finditer(r'[^<>"\']{0,80}name\s*=\s*["\']_t["\'][^<>"\']{0,80}', s):
    print('  ' + re.sub(r'\s+', ' ', m.group(0))[:180])

print('\n' + '=' * 88)
print('⑥ prices.html 为什么 2.1MB')
print('=' * 88)
s = open('prices.html', encoding='utf-8').read()
print('  总字符 %d' % len(s))
for pat in [r'<script[^>]*pricing[^>]*>', r'id="pricing-json"', r'PRICING_DATA\s*=', r'const PRICING']:
    n = len(re.findall(pat, s, re.I))
    if n:
        print('  命中 %s → %d 处' % (pat, n))
i = s.lower().find('pricing.json')
if i > 0:
    print('  片段:', re.sub(r'\s+', ' ', s[max(0, i - 120):i + 80])[:220])
# 最大的单段
parts = re.split(r'(?=<script)', s)
parts.sort(key=len, reverse=True)
for p in parts[:2]:
    print('  最大 script 块长度: %d, 开头: %s' % (len(p), re.sub(r'\s+', ' ', p[:120])))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""暗病细节 part2：img alt / _t 字段 / prices.html 体积 / pricing.json 体积 / 死锚点上下文"""
import glob, json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
htmls = sorted(glob.glob('*.html'))

print('=' * 88)
print('① 缺 alt 的 img 具体是什么')
print('=' * 88)
kinds = collections.Counter()
sample = {}
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'<img\b[^>]*>', s, re.I):
        tag = m.group(0)
        if re.search(r'\balt\s*=\s*["\'][^"\']*["\']', tag, re.I):
            continue
        k = re.search(r'src\s*=\s*["\']([^"\']+)', tag)
        key = k.group(1) if k else tag[:50]
        kinds[key] += 1
        sample.setdefault(key, (f, re.sub(r'\s+', ' ', tag)))
for k, c in kinds.most_common(6):
    print('  [%d 页] %s' % (c, k))
    print('      例: %s' % sample[k][1][:170])

print('\n' + '=' * 88)
print('② booking.html 的 _t 字段')
print('=' * 88)
s = open('booking.html', encoding='utf-8').read()
for m in re.finditer(r'.{0,90}name\s*=\s*["\']_t["\'].{0,60}', s, re.S):
    print('  ' + re.sub(r'\s+', ' ', m.group(0))[:190])

print('\n' + '=' * 88)
print('③ prices.html 体积构成')
print('=' * 88)
s = open('prices.html', encoding='utf-8').read()
print('  总字符 %d  (%.2f MB)' % (len(s), len(s.encode('utf-8')) / 1048576.0))
blocks = re.findall(r'<script\b[^>]*>(.*?)</script>', s, re.S | re.I)
blocks.sort(key=len, reverse=True)
for b in blocks[:3]:
    print('  script 块 %d 字符 (%.0f KB), 开头: %s' % (len(b), len(b) / 1024.0, re.sub(r'\s+', ' ', b[:110])))
print('  正文(去 script) %d 字符' % len(re.sub(r'<script\b[^>]*>.*?</script>', '', s, flags=re.S | re.I)))
# 有多少重复的行
lines = [l.strip() for l in s.split('\n') if l.strip()]
print('  行数 %d，唯一行 %d' % (len(lines), len(set(lines))))

print('\n' + '=' * 88)
print('④ pricing.json 体积与前端加载方式')
print('=' * 88)
pj = open('pricing/pricing.json', encoding='utf-8').read()
print('  pricing.json %.2f MB' % (len(pj.encode('utf-8')) / 1048576.0))
d = json.loads(pj)
print('  城市数 %d' % len(d['cities']))
one = len(json.dumps(d['cities']['beijing'], ensure_ascii=False).encode('utf-8'))
print('  单城(北京) %d 字节 → 331 城 ≈ %.2f MB' % (one, one * 331 / 1048576.0))
print('  字段: ', list(d['cities']['beijing'].keys()))
print('  机场条目样例:', json.dumps(d['cities']['beijing']['airport']['sedan_economy'], ensure_ascii=False))
for f in ['js/booking.js', 'booking.html']:
    s2 = open(f, encoding='utf-8').read()
    for m in re.finditer(r'.{0,80}pricing/pricing\.json.{0,90}', s2, re.S):
        print('  [%s] %s' % (f, re.sub(r'\s+', ' ', m.group(0))[:200]))

print('\n' + '=' * 88)
print('⑤ 城市页 #tea 死锚点上下文 + best-time 重复 id')
print('=' * 88)
for f in ['chongqing.html', 'shanghai.html']:
    s = open(f, encoding='utf-8').read()
    for m in re.finditer(r'.{0,100}#tea.{0,40}', s, re.S):
        print('  [%s] %s' % (f.replace('.html', ''), re.sub(r'\s+', ' ', m.group(0))[:180]))
    ids = re.findall(r'id="([^"]+)"', s)
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    print('  [%s] 重复 id: %s' % (f.replace('.html', ''), dup))
    for m in re.finditer(r'<[^>]*id="best-time"[^>]*>', s):
        print('      ' + re.sub(r'\s+', ' ', m.group(0))[:150])
    break

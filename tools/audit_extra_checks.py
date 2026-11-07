#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补充检查：里程口径 / 发票 / 司机资质 / 价格一致性 / 60分钟是否同步"""
import glob, json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
htmls = sorted(glob.glob('*.html'))


def plain(f):
    s = open(f, encoding='utf-8', errors='ignore').read()
    s = re.sub(r'<script.*?</script>', ' ', s, flags=re.S)
    s = re.sub(r'<style.*?</style>', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', '\n', s)
    for a, b in (('&mdash;', '—'), ('&nbsp;', ' '), ('&amp;', '&'), ('&#39;', "'"),
                 ('&quot;', '"'), ('&yen;', '¥')):
        s = s.replace(a, b)
    return [re.sub(r'\s+', ' ', l).strip() for l in s.split('\n') if re.sub(r'\s+', ' ', l).strip()]


print('=' * 88)
print('① 发票 / invoice 承诺')
print('=' * 88)
for f in htmls:
    for l in plain(f):
        if re.search(r'invoice|receipt for|tax receipt', l, re.I) and len(l) > 25:
            print('  [' + f.replace('.html', '') + '] ' + l[:190])

print('\n' + '=' * 88)
print('② 司机资质 / 保险')
print('=' * 88)
buckets = collections.defaultdict(list)
for f in htmls:
    for l in plain(f):
        for p in [r'licensed[^.]{0,60}', r'insured[^.]{0,60}', r'professional driver[^.]{0,50}',
                  r'background[- ]checked[^.]{0,50}', r'first[- ]aid[^.]{0,40}']:
            for m in re.finditer(p, l, re.I):
                buckets[re.sub(r'\s+', ' ', m.group(0)).strip()].append(f.replace('.html', ''))
for t, fs in sorted(buckets.items(), key=lambda kv: -len(kv[1]))[:14]:
    print('  [' + str(len(set(fs))) + ' 页] ' + t[:110])

print('\n' + '=' * 88)
print('③ 里程口径（35km / 里程包含）')
print('=' * 88)
b2 = collections.defaultdict(list)
for f in htmls:
    for l in plain(f):
        for m in re.finditer(r'[^.]{0,80}35 ?km[^.]{0,80}', l, re.I):
            b2[re.sub(r'\s+', ' ', m.group(0)).strip()[:120]].append(f.replace('.html', ''))
for t, fs in sorted(b2.items(), key=lambda kv: -len(kv[1]))[:14]:
    print('  [' + str(len(set(fs))) + ' 页] ' + t)

print('\n' + '=' * 88)
print('④ 60 分钟（含时长）是否已同步到页面文案')
print('=' * 88)
for kw in ['60 min', '60 minutes']:
    n = sum(1 for f in htmls if kw in open(f, encoding='utf-8', errors='ignore').read())
    print('  含 "%s" 的页面: %d' % (kw, n))

print('\n' + '=' * 88)
print('⑤ 价格一致性抽查：城市页展示价 vs pricing.json 最低价')
print('=' * 88)
d = json.load(open('pricing/pricing.json', encoding='utf-8'))
cities = d['cities']
mis = []
for f in htmls:
    slug = f[:-5]
    if slug not in cities:
        continue
    c = cities[slug]
    vals = [v['pkg'] for v in (c.get('airport') or {}).values() if v.get('pkg')]
    for t in (c.get('charter') or {}).values():
        vals += [x['pkg'] for x in (t.get('tiers') or {}).values() if x.get('pkg')]
    if not vals:
        continue
    lo = min(vals)
    s = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'[¥$]\s?([\d,]{2,7})', s):
        raw = m.group(1).replace(',', '')
        try:
            n = int(raw)
        except ValueError:
            continue
        if n in (lo, round(lo / 7.1), round(lo * 7.1)):
            continue
        if 100 <= n <= 100000 and abs(n - lo) > 2 and abs(n - round(lo / 7.1)) > 2:
            mis.append((slug, n, lo))
            break
print('  展示价与库中最低价不一致的城市页: %d' % len(mis))
for m in mis[:12]:
    print('   ', m)

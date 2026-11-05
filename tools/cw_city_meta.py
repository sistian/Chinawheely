#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽取所有城市页的元数据（幂等，输出 tools/city_meta.json）
抽取项：显示名、机场短名+代码、机场全名+代码、hero 副标题
"""
import json, os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

meta = {}
for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    slug = f[:-5]
    h = open(f, encoding='utf-8', errors='ignore').read()

    # 城市页特征：h1 = 城市名 + <span>Airport Transfer & Private Car</span>
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    if not m or 'Airport Transfer' not in m.group(1):
        continue
    name = re.sub(r'<[^>]+>', '', m.group(1).split('<span')[0])
    name = re.sub(r'\s+', ' ', name).strip()
    if not name or len(name) > 24:
        continue

    # 机场：meta description 里的 "Fixed price <A> (XXX) & <B> (YYY) airport transfers"
    short = []
    md = re.search(r'<meta name="description" content="(.*?)"', h, re.S)
    if md:
        short = re.findall(r'([A-Z][A-Za-z\' ]*?)\s*\(([A-Z]{3})\)', md.group(1))

    # 机场全名：正文里的 "X International Airport (CODE)"
    full = []
    for nm, cd in re.findall(r'((?:[A-Z][A-Za-z\'-]*\s*){0,4}(?:International Airport|Airport|Field))\s*\(([A-Z]{3})\)', h):
        nm = re.sub(r'\s+', ' ', nm).strip()
        if nm and (nm, cd) not in full and len(nm) < 50:
            full.append((nm, cd))

    hero_lead = ''
    mh = re.search(r'<p class="hero-lead[^"]*"[^>]*>(.*?)</p>', h, re.S)
    if mh:
        hero_lead = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', mh.group(1))).strip()

    meta[slug] = {
        'name': name,
        'airports_short': [{'name': a.strip(), 'code': c} for a, c in short],
        'airports_en': [{'name': a.strip(), 'code': c} for a, c in full][:4],
        'hero_lead': hero_lead,
    }

json.dump(meta, open('tools/city_meta.json', 'w'), ensure_ascii=False, indent=1)
print(f'抽取 {len(meta)} 个城市页 → tools/city_meta.json')
for s in ['beijing', 'changsha', 'xian', 'shanghai', 'harbin', 'lhasa']:
    if s in meta:
        m = meta[s]
        print(f"  {s:10s} {m['name']:14s} short={[x['code'] for x in m['airports_short']]} full={[x['name'] for x in m['airports_en']][:2]}")

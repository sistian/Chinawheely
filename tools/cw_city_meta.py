#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从城市页抽取主题页需要复用的城市元数据（幂等，输出 tools/city_meta.json）
抽取项：显示名、hero 图、hero 副标题、机场代码、sibling 链接、价格块
"""
import json, os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

CITIES = ['beijing', 'shanghai', 'guangzhou', 'shenzhen', 'xian', 'wuhan', 'nanjing',
          'tianjin', 'suzhou', 'qingdao', 'jinan', 'harbin', 'xiamen', 'kunming',
          'nanchang', 'zhengzhou', 'chengdu', 'chongqing', 'dalian', 'fuzhou',
          'changsha', 'hefei', 'hangzhou']

meta = {}
for c in CITIES:
    p = f'{c}.html'
    if not os.path.exists(p):
        continue
    h = open(p, encoding='utf-8').read()

    # 显示名：h1 中 <span> 之前的部分（span 是副标题）
    name = c.capitalize()
    if c == 'xian':
        name = "Xi'an"
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    if m:
        t = m.group(1).split('<span')[0]
        t = re.sub(r'<[^>]+>', '', t)
        t = re.sub(r'\s+', ' ', t).strip()
        if t and len(t) <= 24:
            name = t

    # hero 图
    img = ''
    m = re.search(r"url\('(images/[^']+)'\)", h)
    if m:
        img = m.group(1)

    # hero 副标题
    lead = ''
    m = re.search(r'<p class="hero-lead[^"]*"[^>]*>(.*?)</p>', h, re.S)
    if m:
        lead = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip()

    # hero h1 副标题（span）
    sub = ''
    m = re.search(r'<h1[^>]*>.*?<span>(.*?)</span>', h, re.S)
    if m:
        sub = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip()

    # 机场代码
    codes = []
    m = re.search(r'<p class="hero-lead[^"]*"[^>]*>(.*?)</p>', h, re.S)
    if m:
        codes = re.findall(r'\(([A-Z]{3})\)', m.group(1))

    # 机场名（中文机场名 → 英文）
    airports_en = []
    m = re.search(r'(<h2[^>]*>.*?Airport.*?</h2>)', h, re.S)
    if m:
        airports_en = re.findall(r'([A-Z][A-Za-z ]+?)\s*\(([A-Z]{3})\)', m.group(1))

    # 兄弟链接（More X Guides 区块里的卡片）
    sibs = []
    for m in re.finditer(r'<a class="card" href="([^"]+\.html)"[^>]*>.*?<h3[^>]*>(.*?)</h3>',
                         h, re.S):
        sibs.append({'href': m.group(1), 'title': re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(2))).strip()})

    meta[c] = {
        'name': name, 'image': img, 'hero_lead': lead, 'hero_sub': sub,
        'airport_codes': codes,
        'airports_en': [{'name': n.strip(), 'code': cd} for n, cd in airports_en],
        'siblings': sibs,
    }

json.dump(meta, open('tools/city_meta.json', 'w'), ensure_ascii=False, indent=1)
print(f'抽取 {len(meta)} 城 → tools/city_meta.json')
for c in CITIES[:4]:
    m = meta.get(c, {})
    print(f"  {c:10s} name={m.get('name'):12s} img={m.get('image'):26s} codes={m.get('airport_codes')} sibs={len(m.get('siblings', []))}")
print('  ...')
print(f"  beijing hero_lead: {meta['beijing']['hero_lead'][:90]}")
print(f"  beijing hero_sub : {meta['beijing']['hero_sub']}")
print(f"  beijing airports  : {meta['beijing']['airports_en']}")

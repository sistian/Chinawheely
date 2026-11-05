#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汇总主题页内容 JSON → 渲染器读取的 4 个聚合文件
   {family}.json  =  {slug: 页面内容}

来源（全部按 slug 形状判定族，不靠文件名）：
  - theme_content/*.json         （各 agent 交付：airport_a/b, sights_a/b, food_a/b, tea_pages…）
  - theme_content/parts/*.json   （分片）
  - theme_content/pages/*.json    （单页文件，slug 从文件名推断）
坏 JSON 会被跳过并报告，不让一个坏文件毁掉整批。
"""
import glob, json, os

WS = '/Users/w/.openclaw/workspace/theme_content'
FAMS = ['airport', 'sights', 'food', 'tea']


def fam_of(slug):
    if '-airport-transfer-to-' in slug:
        return 'airport'
    if slug.endswith('-day-trips') or slug.endswith('-photo-spots'):
        return 'sights'
    if slug.endswith('-food-shopping'):
        return 'food'
    if slug.endswith('-tea-culture'):
        return 'tea'
    return None


def safe_load(p):
    try:
        d = json.load(open(p, encoding='utf-8'))
        return d if isinstance(d, dict) else None
    except Exception as e:
        print(f'  ✗ 跳过坏文件 {os.path.basename(p)}: {str(e)[:60]}')
        return None


agg = {f: {} for f in FAMS}
src = {}          # slug -> 来源文件
conflicts = []
n_pages = 0


def put(slug, val, origin):
    f = fam_of(slug)
    if not f:
        return
    if slug in agg[f]:
        conflicts.append((slug, src.get(slug), origin))
        return                      # 先到的优先，后来的不覆盖
    agg[f][slug] = val
    src[slug] = origin


# 1) 单页文件（优先级最高：pages/ 是每个 agent 的最新单页交付）
for p in sorted(glob.glob(os.path.join(WS, 'pages', '*.json'))):
    d = safe_load(p)
    if not d:
        continue
    base = os.path.basename(p)[:-5]
    slug = base if fam_of(base) else None
    if not slug:
        cs = d.get('city_slug', '')
        if 'trips' in d:
            slug = f'{cs}-day-trips'
        elif 'spots' in d:
            slug = f'{cs}-photo-spots'
        elif 'markets' in d:
            slug = f'{cs}-food-shopping'
        elif 'airports' in d:
            slug = f'{cs}-airport-transfer-to-{base.split("to-")[-1]}'
        else:
            slug = base
    put(slug, d, 'pages/' + os.path.basename(p))
    n_pages += 1

# 2) 分片
for p in sorted(glob.glob(os.path.join(WS, 'parts', '*.json'))):
    d = safe_load(p)
    if not d:
        continue
    for k, v in d.items():
        put(k, v, 'parts/' + os.path.basename(p))

# 3) 旧聚合文件（theme_content/*.json：airport_a/b, sights_a/b/c, food_a/b/c, tea_pages）
for p in sorted(glob.glob(os.path.join(WS, '*.json'))):
    b = os.path.basename(p)
    if b in ('wiki_cache.json',) or b in [f'{x}.json' for x in FAMS]:
        continue
    d = safe_load(p)
    if not d:
        continue
    for k, v in d.items():
        put(k, v, b)

# 4) 写盘
for f in FAMS:
    out = os.path.join(WS, f'{f}.json')
    json.dump(agg[f], open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'  {f}.json  {len(agg[f])} 页')

print(f'\n合并单页文件 {n_pages} 个')
if conflicts:
    print(f'⚠️ 重名跳过 {len(conflicts)} 处（先到的优先）: {conflicts[:5]}')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 pricing.json 从 53 城（报价单 xlsx 显式值）扩展到全站 333 城。

策略（与既有惯例一致：yinchuan←weihai 的 filledFrom 先例）：
  - 53 个 xlsx 城市保留原值不动（唯一真相源）
  - 其余 280 城 = 同省参照城整块复制（省会优先；甘肃/青海→西安、西藏→成都），
    每城记录 meta.policy.priceFilledFrom[slug] = 参照城 slug
  - 顺带把键 hohhot 统一为站点 slug huhehaote（避免下拉重复）
  - 每城补 prov / provCn 字段（表单按省分组用）
"""
import json, copy, sys, os
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, 'pricing', 'pricing.json'), encoding='utf-8'))
site = json.load(open('/tmp/site_cities.json', encoding='utf-8'))

# hohhot → huhehaote（站点 slug）
if 'hohhot' in d['cities'] and 'huhehaote' not in d['cities']:
    d['cities']['huhehaote'] = d['cities'].pop('hohhot')
if 'yinchuan' in (d['meta'].get('policy', {}).get('priceFilledFrom') or {}):
    pass  # 11-04 的单元格级填充记录保留

# 省会优先的参照城
PROV_REF = {
    'Guangdong': 'guangzhou', 'Fujian': 'fuzhou', 'Jiangsu': 'nanjing',
    'Shandong': 'jinan', 'Liaoning': 'shenyang', 'Henan': 'zhengzhou',
    'Shaanxi': 'xian', 'Hainan': 'haikou', 'Zhejiang': 'hangzhou',
    'Anhui': 'hefei', 'Guangxi': 'nanning', 'Guizhou': 'guiyang',
    'Hebei': 'shijiazhuang', 'Heilongjiang': 'harbin', 'Hubei': 'wuhan',
    'Hunan': 'changsha', 'Inner Mongolia': 'huhehaote', 'Jiangxi': 'nanchang',
    'Jilin': 'changchun', 'Ningxia': 'yinchuan', 'Shanxi': 'taiyuan',
    'Sichuan': 'chengdu', 'Xinjiang': 'urumqi', 'Yunnan': 'kunming',
    'Chongqing': 'chongqing', 'Beijing': 'beijing', 'Shanghai': 'shanghai',
    'Tianjin': 'tianjin',
    # 无定价城的省份 → 邻近大区参照
    'Gansu': 'xian', 'Qinghai': 'xian', 'Tibet': 'chengdu',
}

filled = {}
added = 0
# canonical 指向别页的别名页（bitu→bijie / qiqihar→qiqihaer）不入库，避免下拉重复城市
ALIAS = set(json.load(open('/tmp/alias_pages.json')) if os.path.exists('/tmp/alias_pages.json') else {})
EXCLUDE = {'bitu', 'qiqihar'} | ALIAS
for slug, info in site.items():
    if slug in EXCLUDE:
        continue
    if slug in d['cities']:
        c = d['cities'][slug]
        c.setdefault('cn', info['cn']); c.setdefault('en', info['en'])
        c['prov'] = info['prov']; c['provCn'] = info['provCn']
        continue
    ref = PROV_REF.get(info['prov'])
    if not ref or ref not in d['cities']:
        print('!! 无参照城:', slug, info['prov']); sys.exit(1)
    c = copy.deepcopy(d['cities'][ref])
    c['cn'] = info['cn']; c['en'] = info['en']
    c['prov'] = info['prov']; c['provCn'] = info['provCn']
    d['cities'][slug] = c
    filled[slug] = ref
    added += 1

d['meta']['policy']['priceFilledFrom'] = filled
d['meta']['policy']['allCitiesRule'] = (
    '53 cities priced explicitly from 入境游包车报价单_游客版 2026年 报价单 更新版本.xlsx; '
    'other 280 cities use same-province reference city pricing '
    '(provincial capital preferred; Gansu/Qinghai→xian, Tibet→chengdu)'
)
d['meta']['generatedAt'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
d['meta']['cityCount'] = len(d['cities'])

# ---- 校验 ----
assert len(d['cities']) == 331, f"城市数 {len(d['cities'])} != 331（333 - bitu/qiqihar 别名）"
bad = []
for slug, c in d['cities'].items():
    ap = c.get('airport') or {}
    ch = c.get('charter') or {}
    if len(ap) != 6: bad.append((slug, 'airport', len(ap)))
    if len(ch) != 5: bad.append((slug, 'charter', len(ch)))
    for vk, v in ch.items():
        if len(v.get('tiers') or {}) != 5: bad.append((slug, 'tiers', vk))
    for f in ('cn', 'en', 'prov', 'provCn'):
        if not c.get(f): bad.append((slug, 'missing', f))
if bad:
    print('!! 结构校验失败:', bad[:10]); sys.exit(1)

out = os.path.join(BASE, 'pricing', 'pricing.json')
json.dump(d, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(f"OK {len(d['cities'])} 城（新增 {added}，参照映射 {len(filled)} 条），文件大小 {os.path.getsize(out)//1024} KB")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 pricing.json 的每个城市补 py 字段（中文名全拼，用于下拉按拼音首字母分组）"""
import json, os, re, sys
from pypinyin import lazy_pinyin, Style

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(BASE, 'pricing', 'pricing.json')
d = json.load(open(P, encoding='utf-8'))

# 行政区后缀（去后缀再拼拼音，避免 "beijing shi"）
SUFFIX = re.compile(r'(省|市|地区|自治州|自治区|特别行政区|盟|县|自治县|旗)$')

# 多音字人工校正（pypinyin 默认读音与规范读音不一致）
PINYIN_FIX = {
    'urumqi': 'wulumuqi',    # 乌鲁木齐
    'luohe': 'luohe',        # 漯河
    'yuzhou': 'bozhou',      # 亳州
    'eerduosi': 'eerduosi',  # 鄂尔多斯
    'chaoyang': 'chaoyang',  # 朝阳
    'changzhi': 'changzhi',  # 长治
}

def py_of(slug, cn):
    if slug in PINYIN_FIX:
        return PINYIN_FIX[slug]
    c = SUFFIX.sub('', cn)
    return ''.join(lazy_pinyin(c, style=Style.NORMAL)).lower()

odd = []
for slug, c in d['cities'].items():
    py = py_of(slug, c['cn'])
    if not py or not py[0].isalpha():
        odd.append((slug, c['cn'], py))
    c['py'] = py

if odd:
    print('!! 拼音异常，需人工处理:')
    for o in odd: print('  ', o)
    sys.exit(1)

# 抽样核对
for s in ('beijing', 'lasa', 'sanya', 'xian', 'harbin', 'urumqi', 'xishuangbanna', 'taizhou_js'):
    if s in d['cities']:
        print(f"  {s}: {d['cities'][s]['cn']} → {d['cities'][s]['py']}")

d['meta']['pinyinNote'] = 'py = 中文名全拼（无声调），用于下拉按拼音首字母分组排序'
json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(f"OK {len(d['cities'])} 城已写入 py 字段，文件 {os.path.getsize(P)//1024} KB")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证同名不同城页面是否真区分（内容差异度 + 关键事实）"""
import re, os, difflib, json

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PAIRS = [
    ('yulin_sx.html', 'yulin.html', '榆林(陕西) vs 玉林(广西)'),
    ('fuzhou_jx.html', 'fuzhou.html', '抚州(江西) vs 抚州(福建)'),
    ('suzhou_ah.html', 'suzhou.html', '宿州(安徽) vs 苏州(江苏)'),
    ('yichun_hlj.html', 'yichun.html', '伊春(黑龙江) vs 宜春(江西)'),
    ('taizhou_js.html', 'taizhou.html', '泰州(江苏) vs 台州(浙江)'),
]


def text(f):
    s = open(f, encoding='utf-8', errors='ignore').read()
    s = re.sub(r'<script.*?</script>', ' ', s, flags=re.S)
    s = re.sub(r'<style.*?</style>', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def facts(f):
    s = open(f, encoding='utf-8', errors='ignore').read()
    ti = re.search(r'<title>(.*?)</title>', s, re.S)
    de = re.search(r'name="description" content="([^"]*)"', s)
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S)
    aps = sorted(set(re.findall(r'\(([A-Z]{3})\)', s)))[:6]
    prices = sorted(set(int(x.replace(',', '')) for x in re.findall(r'¥\s?([\d,]{3,6})', s)))[:6]
    return {
        'title': (ti.group(1) if ti else '')[:70],
        'desc': (de.group(1) if de else '')[:100],
        'h1': re.sub(r'<[^>]+>', '', (h1.group(1) if h1 else '')).strip()[:60],
        'airports': aps,
        'prices': prices,
    }


for a, b, label in PAIRS:
    ta, tb = text(a), text(b)
    r = difflib.SequenceMatcher(None, ta[:6000], tb[:6000]).ratio()
    print('\n' + '=' * 84)
    print('%s   正文相似度 %.1f%%' % (label, r * 100))
    print('=' * 84)
    for f in (a, b):
        d = facts(f)
        print('  %-18s' % f.replace('.html', ''))
        print('      title: ' + d['title'])
        print('      h1   : ' + d['h1'])
        print('      机场 : ' + ', '.join(d['airports']))
        print('      价格 : ' + ', '.join(str(x) for x in d['prices']))

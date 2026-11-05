#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓 10 个已合并城市的维基正文（en + zh），落 raw/c/，并抽出含「茶」的句子。"""
import os, re, json, time, urllib.request, urllib.parse

P = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
op = urllib.request.build_opener(urllib.request.ProxyHandler(P))
UA = {'User-Agent': 'ChinawheelyResearch/1.0 (SEO content verification; 15527771775@qq.com)'}
HOSTS = {'en': 'en.wikipedia.org', 'zh': 'zh.wikipedia.org'}
OUT = '/Users/w/.openclaw/workspace/theme_content/raw/c'
os.makedirs(OUT, exist_ok=True)


def _get(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            return json.loads(op.open(req, timeout=60).read())
        except Exception as e:
            if '429' in str(e):
                time.sleep(6 * (i + 1)); continue
            raise
    return {}


def extract(lang, title):
    kw = {'action': 'query', 'format': 'json', 'prop': 'extracts',
          'explaintext': 1, 'redirects': 1, 'titles': title}
    u = f'https://{HOSTS[lang]}/w/api.php?' + urllib.parse.urlencode(kw)
    d = _get(u)
    for p in d.get('query', {}).get('pages', {}).values():
        return '' if 'missing' in p else p.get('extract', '')
    return ''


PAIRS = [
    ('shanghai', 'Shanghai', '上海'), ('tianjin', 'Tianjin', '天津'),
    ('wuhan', 'Wuhan', '武汉'), ('harbin', 'Harbin', '哈尔滨'),
    ('dalian', 'Dalian', '大连'), ('jinan', 'Jinan', '济南'),
    ('qingdao', 'Qingdao', '青岛'), ('chongqing', 'Chongqing', '重庆'),
    ('shenzhen', 'Shenzhen', '深圳'), ('xian', "Xi'an", '西安'),
]

for slug, en, zh in PAIRS:
    for lang, title in (('zh', zh), ('en', en)):
        p = os.path.join(OUT, f'{slug}_{lang}.txt')
        if os.path.exists(p) and os.path.getsize(p) > 800:
            continue
        try:
            txt = extract(lang, title)
        except Exception as e:
            print(f'  {slug}/{lang} 抓取失败 {str(e)[:40]}'); continue
        if txt:
            open(p, 'w', encoding='utf-8').write(txt)
            print(f'  ✓ {slug}/{lang} {len(txt)} 字')
        else:
            print(f'  ✗ {slug}/{lang} 空')
        time.sleep(2.5)

print('\n=== 含「茶」的句子 ===\n')
for slug, en, zh in PAIRS:
    hits = []
    for lang in ('zh', 'en'):
        p = os.path.join(OUT, f'{slug}_{lang}.txt')
        if not os.path.exists(p):
            continue
        t = open(p, encoding='utf-8', errors='ignore').read()
        for s in re.split(r'(?<=[。！？\n])', t):
            s = s.strip()
            if ('茶馆' in s or '茶楼' in s or '饮茶' in s or '喝茶' in s
                    or '茶文化' in s or 'teahouse' in s.lower()
                    or 'tea house' in s.lower()) and 12 <= len(s) <= 240:
                hits.append((lang, s))
    print(f'--- {slug} ({len(hits)} 句) ---')
    for lang, s in hits[:8]:
        print(f'   [{lang}] {s[:210]}')
    print()

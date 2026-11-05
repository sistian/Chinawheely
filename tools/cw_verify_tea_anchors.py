#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核实 10 个已合并城市的「茶」锚点条目是否真实存在并抓正文。
只抓下面这张表里的条目；抓不到（missing）就说明不能写。
"""
import os, re, json, time, urllib.request, urllib.parse

P = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
op = urllib.request.build_opener(urllib.request.ProxyHandler(P))
UA = {'User-Agent': 'ChinawheelyResearch/1.0 (SEO content verification; 15527771775@qq.com)'}
HOSTS = {'en': 'en.wikipedia.org', 'zh': 'zh.wikipedia.org'}
OUT = '/Users/w/.openclaw/workspace/theme_content/raw/t2'
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


# (城市, 语言, 条目名, 它要证明的事)
PLAN = [
    ('qingdao',  'zh', '崂山绿茶',   '崂山绿茶产于青岛崂山，青岛本地茶'),
    ('xian',     'zh', '泾阳茯茶',   '泾阳茯茶产于陕西泾阳，西安周边'),
    ('harbin',   'zh', '老都一处',   '哈尔滨老字号的茶楼/饭店'),
    ('tianjin',  'zh', '天津早点',   '天津早茶/茶社文化'),
    ('chongqing','zh', '盖碗茶',     '盖碗茶与重庆街头茶馆'),
    ('jinan',    'zh', '趵突泉',     '济南泉水与茶'),
    ('shanghai', 'zh', '湖心亭',     '上海湖心亭茶楼（上海最老茶楼）'),
    ('shenzhen', 'zh', '饮茶',       '广东饮茶/早茶体系'),
    ('dalian',   'zh', '大连市',     '大连概况'),
    ('wuhan',    'zh', '茶馆',       '中国茶馆通史（武汉已有）'),
]

for city, lang, title, why in PLAN:
    p = os.path.join(OUT, f'{city}__{title}.txt')
    if os.path.exists(p) and os.path.getsize(p) > 300:
        txt = open(p, encoding='utf-8').read()
    else:
        try:
            txt = extract(lang, title)
        except Exception as e:
            print(f'  ✗ {city} {title}: {str(e)[:40]}'); continue
        if txt:
            open(p, 'w', encoding='utf-8').write(txt)
        time.sleep(2.5)
    if not txt:
        print(f'  ✗ {city:10s} {title:10s} 不存在 —— 不能写')
        continue
    # 抽出含关键词的句子
    kws = ['茶', '崂山', '茯茶', '泉', '早茶', '楼', '馆']
    hits = [s.strip() for s in re.split(r'(?<=[。！？\n])', txt)
            if any(k in s for k in kws) and 15 <= len(s.strip()) <= 200]
    print(f'  ✓ {city:10s} {title:10s} {len(txt):6d}字  用途: {why}')
    for h in hits[:3]:
        print(f'       · {h[:170]}')
    print()

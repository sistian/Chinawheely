#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 10 个已合并的城市查「茶馆/茶楼」相关维基条目，落到 raw/t/ 下。
每城先试若干已知名，再退回中文维基搜索，把真实存在的条目正文存下来。
"""
import os, sys, json, time, urllib.request, urllib.parse

P = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
op = urllib.request.build_opener(urllib.request.ProxyHandler(P))
UA = {'User-Agent': 'ChinawheelyResearch/1.0 (SEO content verification; 15527771775@qq.com)'}
HOSTS = {'en': 'en.wikipedia.org', 'zh': 'zh.wikipedia.org'}
OUT = '/Users/w/.openclaw/workspace/theme_content/raw/t'
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


def api(lang, **kw):
    kw.update({'action': 'query', 'format': 'json'})
    u = f'https://{HOSTS[lang]}/w/api.php?' + urllib.parse.urlencode(kw)
    return _get(u)


def extract(lang, title):
    d = api(lang, prop='extracts', explaintext=1, redirects=1, titles=title)
    for p in d.get('query', {}).get('pages', {}).values():
        if 'missing' in p:
            return ''
        return p.get('extract', '')
    return ''


def search(lang, q, limit=8):
    d = api(lang, list='search', srsearch=q, srlimit=limit)
    return [x['title'] for x in d.get('query', {}).get('search', [])]


TARGETS = {
    'shanghai':   ['湖心亭', '上海茶馆', '茶馆'],
    'tianjin':    ['广东会馆', '谦祥益', '天津茶馆'],
    'wuhan':      ['老谦记', '武汉茶馆', '楚茶'],
    'harbin':     ['老都一处', '哈尔滨茶馆', '茶馆'],
    'dalian':     ['大连茶馆', '茶馆', '大连'],
    'jinan':      ['趵突泉', '泉城茶社', '济南茶馆'],
    'qingdao':    ['劈柴院', '青岛茶馆', '茶馆'],
    'chongqing':  ['洞子茶馆', '重庆茶馆', '茶馆'],
    'shenzhen':   ['深圳茶馆', '茶馆', '深圳'],
    'xian':       ['湘子庙', '西安茶馆', '茶馆'],
}

for city, names in TARGETS.items():
    got = []
    for n in names:
        txt = extract('zh', n)
        if len(txt) > 400:
            p = os.path.join(OUT, f'{city}__{n}.txt')
            open(p, 'w', encoding='utf-8').write(txt)
            got.append((n, len(txt)))
            time.sleep(2)
            break
        time.sleep(1.5)
    if not got:
        # 退回搜索
        for n in names[:1]:
            try:
                cands = search('zh', f'{n}')
            except Exception:
                cands = []
            for c in cands:
                if any(k in c for k in ('茶', '馆', '会馆')):
                    txt = extract('zh', c)
                    if len(txt) > 400:
                        open(os.path.join(OUT, f'{city}__{c}.txt'), 'w',
                             encoding='utf-8').write(txt)
                        got.append((c, len(txt)))
                        break
                time.sleep(1.5)
    print(f'{city:12s} → {got if got else "（没查到）"}')

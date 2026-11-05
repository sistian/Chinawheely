#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二轮：按城市检索真实的茶馆/茶楼条目。
搜索式：'{city}茶馆' / '{city}茶楼' / '{city} 茶'，取搜索结果里像专馆的条目抓正文。
"""
import os, json, time, urllib.request, urllib.parse

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


def search(lang, q, limit=12):
    d = api(lang, list='search', srsearch=q, srlimit=limit)
    return [x['title'] for x in d.get('query', {}).get('search', [])]


CITIES = {
    'shanghai': '上海', 'tianjin': '天津', 'wuhan': '武汉', 'harbin': '哈尔滨',
    'dalian': '大连', 'jinan': '济南', 'qingdao': '青岛', 'chongqing': '重庆',
    'shenzhen': '深圳', 'xian': '西安',
}

for slug, zh in CITIES.items():
    have = set(os.listdir(OUT))
    saved = []
    for q in (f'{zh}茶馆', f'{zh}茶楼', f'{zh} 茶文化', f'{zh} 盖碗茶'):
        try:
            cands = search('zh', q)
        except Exception as e:
            print('  搜索失败', q, str(e)[:50]); continue
        time.sleep(2)
        for c in cands[:6]:
            fn = f'{slug}__{c}.txt'
            if fn in have:
                saved.append((c, '已有')); continue
            try:
                txt = extract('zh', c)
            except Exception:
                continue
            time.sleep(1.5)
            if len(txt) > 800:
                open(os.path.join(OUT, fn), 'w', encoding='utf-8').write(txt)
                saved.append((c, len(txt)))
                break
        if len([x for x in saved if isinstance(x[1], int)]) >= 2:
            break
    print(f'{slug:12s} ({zh}) → {saved[:5]}')

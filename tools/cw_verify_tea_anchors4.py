#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最后一批：万里茶道 + 大连/哈尔滨条目里的茶相关事实。"""
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


for slug, titles in [('tearoad', ['万里茶道', '茶马古道']),
                     ('dalian', ['大连', '大连市历史']),
                     ('harbin', ['哈尔滨', '中东铁路'])]:
    for t in titles:
        p = os.path.join(OUT, f'{slug}__{t}.txt')
        if os.path.exists(p) and os.path.getsize(p) > 300:
            txt = open(p, encoding='utf-8').read()
        else:
            try:
                txt = extract('zh', t)
            except Exception as e:
                print(f'  ✗ {slug} {t}: {str(e)[:40]}'); continue
            if txt:
                open(p, 'w', encoding='utf-8').write(txt)
            time.sleep(2.5)
        if not txt:
            print(f'  ✗ {slug:9s} {t:10s} 不存在')
            continue
        hits = [s.strip() for s in re.split(r'(?<=[。！？\n])', txt)
                if '茶' in s and 15 <= len(s.strip()) <= 210]
        print(f'  ✓ {slug:9s} {t:10s} {len(txt):6d}字  含茶句 {len(hits)}')
        for h in hits[:5]:
            print(f'       · {h[:190]}')
        break
    print()

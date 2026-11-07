#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sitemap / robots / 索引一致性 + 跳转桩 + 埋点 检查"""
import glob, os, re, json, collections, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
htmls = sorted(glob.glob('*.html'))

print('=' * 84)
print('① sitemap.xml ↔ 实际页面')
print('=' * 84)
sm = open('sitemap.xml', encoding='utf-8').read()
locs = re.findall(r'<loc>(.*?)</loc>', sm)
sm_files = set()
for u in locs:
    path = urllib.parse.urlparse(u).path.lstrip('/')
    if path:
        sm_files.add(path)
real = set(htmls)
# 排除 noindex 页
noindex = set()
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    if re.search(r'<meta[^>]+name\s*=\s*["\']robots["\'][^>]*noindex', s, re.I) or 'noindex' in s[:4000]:
        noindex.add(f)
print('  sitemap 条目 %d' % len(locs))
print('  实际 HTML %d' % len(real))
missing = sorted(x for x in sm_files if x not in real)
print('  sitemap 指向不存在的页面: %d %s' % (len(missing), missing[:8]))
not_in_sm = sorted(x for x in real if x not in sm_files)
print('  存在但不在 sitemap 的页面: %d' % len(not_in_sm))
for x in not_in_sm[:25]:
    tag = ' [noindex]' if x in noindex else ''
    print('      %-30s%s' % (x, tag))
dup_locs = [k for k, v in collections.Counter(locs).items() if v > 1]
print('  sitemap 重复 loc: %d %s' % (len(dup_locs), dup_locs[:5]))

print('\n' + '=' * 84)
print('② robots.txt')
print('=' * 84)
rb = open('robots.txt', encoding='utf-8').read()
print('  ' + re.sub(r'\n+', '\n  ', rb.strip())[:600])

print('\n' + '=' * 84)
print('③ 跳转桩页（别名/重复内容）是否都有 meta refresh + canonical')
print('=' * 84)
stubs = []
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    if 'http-equiv="refresh"' in s.lower():
        stubs.append(f)
print('  跳转桩 %d 个' % len(stubs))
for f in stubs:
    s = open(f, encoding='utf-8', errors='ignore').read()
    m = re.search(r'url=([^"\'>\s]+)', s, re.I)
    c = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', s, re.I)
    tgt = m.group(1) if m else '?'
    tgtf = tgt.lstrip('/').split('/')[-1] if tgt != '?' else '?'
    ok = os.path.exists(tgtf) if tgtf != '?' else False
    can = c.group(1) if c else '缺失'
    flag = '' if ok else '  ⚠ 目标不存在'
    print('  %-24s → %-26s canonical=%-34s%s' % (f.replace('.html', ''), tgt[:26], can[:34], flag))

print('\n' + '=' * 84)
print('④ 埋点：js/analytics.js 事件与 GA ID 配置')
print('=' * 84)
a = open('js/analytics.js', encoding='utf-8').read()
m = re.search(r'GA_MEASUREMENT_ID\s*=\s*["\']([^"\']*)["\']', a)
print('  GA_MEASUREMENT_ID =', m.group(1) if m else '未找到（空 = 静默降级，暂未启用统计）')
print('  事件:', sorted(set(re.findall(r"trackEvent\(\s*['\"]([^'\"]+)", a)))[:15])
for f in ['booking.html', 'contact.html', 'index.html']:
    s = open(f, encoding='utf-8', errors='ignore').read()
    print('  %-14s 引用 analytics.js: %s' % (f, 'analytics.js' in s))

print('\n' + '=' * 84)
print('⑤ CSP：外链资源是否都在白名单里')
print('=' * 84)
for f in ['index.html', 'booking.html', 'contact.html']:
    s = open(f, encoding='utf-8', errors='ignore').read()
    m = re.search(r'<meta[^>]+http-equiv=["\']Content-Security-Policy["\'][^>]*content=["\']([^"\']+)["\']', s, re.I)
    print('  [%s] %s' % (f, (m.group(1)[:260] if m else '无 CSP')))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主题页合并：把 best-time(23) + tea-culture(10) 合并进城市页
 - 给城市页的 Best Time / Tea 段落补稳定锚点 id
 - 生成 301 映射（供 cw_write_redirects.py 写入 vercel.json）
 - 从 sitemap 移除被合并的页
 - 修掉 "Guide inWuhan" 这类缺空格的排版 bug
幂等：可重复运行。
"""
import json, os, re, sys

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

# ---- 主题页城市清单（23 城）----
CITIES = ['beijing', 'shanghai', 'guangzhou', 'shenzhen', 'xian', 'wuhan', 'nanjing',
          'tianjin', 'suzhou', 'qingdao', 'jinan', 'harbin', 'xiamen', 'kunming',
          'nanchang', 'zhengzhou', 'chengdu', 'chongqing', 'dalian', 'fuzhou',
          'changsha', 'hefei', 'hangzhou']

DISPLAY = {'xian': 'Xi\'an'}

# ---- 合并清单 ----
MERGE_BEST_TIME = [f'{c}-best-time' for c in CITIES]                       # 23
MERGE_TEA = [f'{c}-tea-culture' for c in
             ['wuhan', 'dalian', 'harbin', 'tianjin', 'shanghai', 'shenzhen',
              'jinan', 'qingdao', 'chongqing', 'xian']]                       # 10
MERGED = set(MERGE_BEST_TIME) | set(MERGE_TEA)

NAME = {c: DISPLAY.get(c, c.capitalize()) for c in CITIES}

log = []

# ---------- 1. 城市页锚点 ----------
for c in CITIES:
    p = f'{c}.html'
    if not os.path.exists(p):
        continue
    h = open(p, encoding='utf-8').read()
    orig = h

    # 1a. Best Time 段：确保 <section ... id="best-time">
    if 'id="best-time"' not in h:
        m = re.search(r'(<section\b[^>]*>)(?=(?:(?!</?section\b).)*?Best Time to Visit)',
                      h, re.S | re.I)
        if m:
            tag = m.group(1)
            if 'id=' not in tag:
                h = h[:m.start(1)] + tag[:-1] + ' id="best-time">' + h[m.end(1):]
                log.append(f'{p}: Best Time 段加 id="best-time"')

    # 1b. Tea 段：确保有 id="tea"
    if 'id="tea"' not in h:
        m = re.search(r'(<section\b[^>]*>)(?=(?:(?!</?section\b).)*?Tea House Guide in)',
                      h, re.S | re.I)
        if m:
            tag = m.group(1)
            if 'id=' not in tag:
                h = h[:m.start(1)] + tag[:-1] + ' id="tea">' + h[m.end(1):]
                log.append(f'{p}: Tea 段加 id="tea"')

    # 1c. 排版 bug： "Guide inWuhan" → "Guide in Wuhan"
    h2 = re.sub(r'(Tea (?:Culture &amp; )?Tea House Guide in)(?=[A-Z])', r'\1 ', h)
    if h2 != h:
        log.append(f'{p}: 修复 "Guide inXXX" 缺空格')
        h = h2

    if h != orig:
        open(p, 'w', encoding='utf-8').write(h)

# ---------- 2. 301 映射 ----------
plan = {}
for slug in sorted(MERGED):
    if slug.endswith('-best-time'):
        c = slug[:-len('-best-time')]
        plan[slug] = f'/{c}.html#best-time'
    else:
        c = slug[:-len('-tea-culture')]
        plan[slug] = f'/{c}.html#tea'
json.dump(plan, open('tools/theme_merge_plan.json', 'w'), ensure_ascii=False, indent=1)

# ---------- 3. sitemap 移除 ----------
sm_path = 'sitemap.xml'
sm = open(sm_path, encoding='utf-8').read()
before = sm.count('<url>')
for slug in MERGED:
    sm = re.sub(r'<url>\s*<loc>[^<]*' + re.escape(slug) + r'\.html</loc>.*?</url>\s*', '', sm, flags=re.S)
after = sm.count('<url>')
open(sm_path, 'w', encoding='utf-8').write(sm)
log.append(f'sitemap.xml: {before} → {after} 条（移除 {before - after}）')

# ---------- 4. 兄弟链接清理 ----------
# 主题页里的 "Other X Guides" 列表要去掉已合并的项
for slug in MERGED:
    p = slug + '.html'
    if not os.path.exists(p):
        continue
    h = open(p, encoding='utf-8').read()
    o = h
    h = re.sub(r'\s*<li><a href="' + re.escape(slug) + r'\.html">.*?</a></li>', '', h, flags=re.S)
    if h != o:
        open(p, 'w', encoding='utf-8').write(h)
        log.append(f'{p}: 移除自身兄弟链接条目')

# 城市页里的 "Other X Guides" / 卡片链接要去掉已合并的项
for c in CITIES:
    p = f'{c}.html'
    if not os.path.exists(p):
        continue
    h = open(p, encoding='utf-8').read()
    o = h
    for slug in MERGED:
        if slug.startswith(c + '-'):
            anchor = 'best-time' if slug.endswith('-best-time') else 'tea'
            target = f'{c}.html#{anchor}'
            # 兄弟列表项（"Other X Guides"）—— 去掉已合并的
            h = re.sub(r'\s*<li><a href="' + re.escape(slug) + r'\.html">.*?</a></li>', '', h, flags=re.S)
            # 卡片 / 普通链接 —— 改为指向城市页对应锚点，保留内链
            h = h.replace(f'href="{slug}.html"', f'href="{target}"')
    if h != o:
        open(p, 'w', encoding='utf-8').write(h)
        log.append(f'{p}: 清理指向已合并页的链接')

print('\n'.join(f'  · {x}' for x in log) if log else '  (无变化)')
print(f'\n合并计划 {len(plan)} 条 → tools/theme_merge_plan.json')
for k, v in sorted(plan.items()):
    print(f'   /{k}.html → {v}')

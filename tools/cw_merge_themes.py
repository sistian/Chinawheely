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
BASE_URL = 'https://www.chinawheely.com'

BT_H2 = r'<h2[^>]*>[^<]*(?:Best Time|Seasons Overview|When to Visit|Climate)[^<]*</h2>'
TEA_H2 = r'<h2[^>]*>[^<]*Tea\s*h?ouse Guide in[^<]*</h2>'


def ensure_anchor(h, h2_pat, want):
    """找到含 h2_pat 的最近 <section>；若无 id 则加 id=want。
    返回 (html, 实际使用的锚点名)；找不到返回 (html, None)"""
    m = re.search(h2_pat, h, re.I)
    if not m:
        return h, None
    secs = list(re.finditer(r'<section\b[^>]*>', h[:m.start()]))
    if not secs:
        return h, None
    sec = secs[-1]
    tag = sec.group(0)
    mi = re.search(r'id="([^"]+)"', tag)
    if mi:
        return h, mi.group(1)
    h = h[:sec.start()] + tag[:-1] + f' id="{want}">' + h[sec.end():]
    return h, want


# ---------- 1. 城市页锚点（动态发现） ----------
anchors = {}
for c in CITIES:
    p = f'{c}.html'
    if not os.path.exists(p):
        continue
    h = open(p, encoding='utf-8').read()
    orig = h

    h, a_bt = ensure_anchor(h, BT_H2, 'best-time')
    if a_bt and 'id="best-time"' not in orig:
        log.append(f'{p}: Best Time 段加 id="best-time"')
    h, a_tea = ensure_anchor(h, TEA_H2, 'tea')
    if a_tea and 'id="tea"' not in orig:
        log.append(f'{p}: Tea 段加 id="tea"')

    h2 = re.sub(r'(Tea\s*h?ouse Guide in)(?=[A-Z])', r'\1 ', h)
    if h2 != h:
        log.append(f'{p}: 修复 "Guide inXXX" 缺空格')
        h = h2

    if h != orig:
        open(p, 'w', encoding='utf-8').write(h)
    anchors[c] = {'best-time': a_bt, 'tea': a_tea}

# ---------- 2. 301 映射 ----------
plan = {}
for slug in sorted(MERGED):
    if slug.endswith('-best-time'):
        c = slug[:-len('-best-time')]
        a = anchors.get(c, {}).get('best-time')
        if a:
            plan[slug] = f'/{c}.html#{a}'
    else:
        c = slug[:-len('-tea-culture')]
        a = anchors.get(c, {}).get('tea')
        if a:
            plan[slug] = f'/{c}.html#{a}'
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
            target = f'{c}.html#{anchors.get(c, {}).get(anchor, anchor)}'
            # 兄弟列表项（"Other X Guides"）—— 去掉已合并的
            h = re.sub(r'\s*<li><a href="' + re.escape(slug) + r'\.html">.*?</a></li>', '', h, flags=re.S)
            # 卡片 / 普通链接 —— 改为指向城市页对应锚点，保留内链
            h = h.replace(f'href="{slug}.html"', f'href="{target}"')
    if h != o:
        open(p, 'w', encoding='utf-8').write(h)
        log.append(f'{p}: 清理指向已合并页的链接')

# ---------- 4. 站内链接全站清扫 ----------
# 任何页面（含主题页彼此的 sibling 列表）指向已合并页的链接 → 改指城市页锚点
anchor_of = {}
for slug, target in plan.items():
    c = slug.rsplit('-best-time', 1)[0] if slug.endswith('-best-time') else slug[:-len('-tea-culture')]
    anchor_of[slug] = target.split('#', 1)[1] if '#' in target else ''

swept = 0
for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    h = open(f, encoding='utf-8').read()
    o = h
    for slug, target in plan.items():
        c = slug.rsplit('-best-time', 1)[0] if slug.endswith('-best-time') else slug[:-len('-tea-culture')]
        h = h.replace(f'href="{slug}.html"', f'href="{c}.html#{anchor_of[slug]}"')
        h = h.replace(f"href='{slug}.html'", f'href="{c}.html#{anchor_of[slug]}"')
    if h != o:
        open(f, 'w', encoding='utf-8').write(h)
        swept += 1
log.append(f'全站链接清扫：{swept} 页')

# ---------- 5. 已合并页自身：noindex + canonical 指向目标 ----------
for slug, target in plan.items():
    p = slug + '.html'
    if not os.path.exists(p):
        continue
    h = open(p, encoding='utf-8').read()
    o = h
    if 'name="robots"' in h:
        h = re.sub(r'(<meta name="robots" content=")[^"]*(")', r'\1noindex, follow\2', h)
    else:
        h = h.replace('<link rel="canonical"', '<meta name="robots" content="noindex, follow">\n  <link rel="canonical"', 1)
    h = re.sub(r'(<link rel="canonical" href=")[^"]*(")',
               lambda m: m.group(1) + f'{BASE_URL}{target}' + m.group(2), h, count=1)
    if h != o:
        open(p, 'w', encoding='utf-8').write(h)
log.append(f'已合并页 {len(plan)} 个设为 noindex + canonical 指向目标')

print('\n'.join(f'  · {x}' for x in log) if log else '  (无变化)')
print(f'\n合并计划 {len(plan)} 条 → tools/theme_merge_plan.json')
for k, v in sorted(plan.items()):
    print(f'   /{k}.html → {v}')

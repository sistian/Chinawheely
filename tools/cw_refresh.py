#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内容落地 → 渲染 → 体检 一条龙。

用法：python3 tools/cw_refresh.py
做四件事：
  1) 合并所有 agent 产出 → airport/sights/food/tea 四个聚合 JSON
  2) 渲染主题页（幂等）
  3) 体检已渲染页（词数/h2/JSON-LD/<main>/无 seo-keywords）
  4) 跑主题页审计
"""
import os, re, json, subprocess, sys

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)
PY = sys.executable


def run(desc, cmd):
    print(f'\n=== {desc} ' + '=' * (58 - len(desc)))
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = (r.stdout or '') + (r.stderr or '')
    lines = out.strip().split('\n')
    for l in lines[-14:]:
        print('  ' + l)
    return r.returncode, out


run('1/4 合并内容', f'{PY} tools/cw_merge_content.py')
run('2/4 渲染主题页', f'{PY} tools/cw_theme_render.py')

# 3/4 体检
print('\n=== 3/4 已渲染页体检 ' + '=' * 43)
WS = '/Users/w/.openclaw/workspace/theme_content'
agg = {}
for fam in ['airport', 'sights', 'food', 'tea']:
    p = f'{WS}/{fam}.json'
    if os.path.exists(p):
        agg.update(json.load(open(p, encoding='utf-8')))


def body_of(h):
    m = re.search(r'<main\b.*?>(.*?)</main>', h, re.S | re.I)
    return m.group(1) if m else ''


def text_of(b):
    b = re.sub(r'<script.*?</script>', ' ', b, flags=re.S | re.I)
    b = re.sub(r'<style.*?</style>', ' ', b, flags=re.S | re.I)
    b = re.sub(r'<[^>]+>', ' ', b)
    return re.sub(r'\s+', ' ', b).strip()


bad, ok = [], 0
for slug in sorted(agg):
    p = f'{slug}.html'
    if not os.path.exists(p):
        bad.append((slug, ['缺页'])); continue
    h = open(p, encoding='utf-8').read()
    n = len(text_of(body_of(h)).split())
    h2 = len(re.findall(r'<h2\b', h, re.I))
    ld = len(re.findall(r'application/ld\+json', h))
    prob = []
    if n < 900: prob.append(f'词数{n}')
    if h2 < 4: prob.append(f'h2={h2}')
    if ld < 4: prob.append(f'ld={ld}')
    if '<main' not in h: prob.append('无main')
    if 'seo-keywords' in h: prob.append('seo-keywords')
    if prob:
        bad.append((slug, prob))
    else:
        ok += 1
print(f'  已渲染 {len(agg)} 页，达标 {ok} 页，不达标 {len(bad)} 页')
for s, pr in bad[:25]:
    print(f'    ✗ {s:52s} {", ".join(pr)}')
if len(bad) > 25:
    print(f'    … 还有 {len(bad)-25} 页')

run('4/4 主题页审计', f'{PY} tools/cw_audit_theme.py')

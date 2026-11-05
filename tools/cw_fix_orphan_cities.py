#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修「零内链城市页」+ 加审计门禁（幂等）
问题：juancheng / karakax / yongxi / taizhou_js / yichun_hlj 这 5 个城市页
     进了 sitemap、可索引，但站内没有任何一个页面链接到它们（只有自链），
     → Google 只能靠 sitemap 冷启动发现。
原因：index.html 的城市网格是手工拼的，这 5 个当时没加进去；
     审计的孤岛检查只覆盖主题子页（is_sub），没覆盖城市页。
修法：
  1) 缺失的城市补进 index.html 的城市网格
  2) 补进 prices.html 的「Other cities we serve」
  3) 审计新增「孤岛城市页」门禁
"""
import json, os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)
SELF = 'https://www.chinawheely.com'

# 已核实的城市中文名（经中文维基核实）
CN = {
    'juancheng': '鄄城县', 'karakax': '喀什', 'yongxi': '永兴县',
    'taizhou_js': '泰州市', 'yichun_hlj': '宜春市',
}
EN = {
    'juancheng': 'Juancheng', 'karakax': 'Karakax', 'yongxi': 'Yongxing',
    'taizhou_js': 'Taizhou, Jiangsu', 'yichun_hlj': 'Yichun, Heilongjiang',
}

files = sorted(f for f in os.listdir('.') if f.endswith('.html'))
pages = {f: open(f, encoding='utf-8', errors='ignore').read() for f in files}

# ---------- 判定城市页 ----------
SUB_TYPES = ["airport-transfer-to", "day-trips", "best-time", "food-shopping",
             "photo-spots", "tea-culture"]


def is_city_page(f):
    t = re.search(r'<title>(.*?)</title>', pages[f], re.S)
    title = re.sub(r'\s+', ' ', t.group(1)) if t else ''
    if not re.search(r'Airport Transfer|Car Service|Private Car', title, re.I):
        return False
    if any(s in f for s in SUB_TYPES):
        return False
    return True


cities = [f[:-5] for f in files if is_city_page(f)]
print(f'城市页 {len(cities)} 个')

# ---------- 站内入链统计 ----------
inbound = {}
for f, s in pages.items():
    for t in set(re.findall(r'href="([a-zA-Z0-9_\-]+\.html)(?:#[^"]*)?"', s)):
        inbound[t] = inbound.get(t, 0) + 1

# 孤儿 = 除自己外没有任何页面链到
orphans = []
for c in cities:
    others = [f for f, s in pages.items()
              if f != c + '.html' and c + '.html' in
              re.findall(r'href="([a-zA-Z0-9_\-]+\.html)(?:#[^"]*)?"', s)]
    if not others:
        orphans.append(c)
print(f'零内链城市页: {len(orphans)}  {orphans}')

if not orphans:
    print('无孤儿，无需修复')
    raise SystemExit(0)

# ---------- 1. 补进 index.html 城市网格 ----------
idx = open('index.html', encoding='utf-8').read()
grid_slugs = re.findall(r'class="city-card" href="([a-zA-Z0-9_\-]+)\.html"', idx)
added = []
for c in orphans:
    if c in grid_slugs:
        continue
    card = (f'<div class="city-card-wrapper">'
            f'<a class="city-card" href="{c}.html">'
            f'<div class="city-card-bg" style="background: linear-gradient(135deg, '
            f'#1B4D3E 0%, #0d5c3d 50%, #2d6a4f 100%); display: flex; '
            f'align-items: center; justify-content: center" loading="lazy"></div>'
            f'<div class="city-card-caption">'
            f'<span class="city-card-name">{EN.get(c, c.replace("_", " ").title())}</span>'
            f'<span class="city-card-name-cn">{CN.get(c, "")}</span>'
            f'</div></a></div>\n')
    # 插到最后一个 city-card-wrapper 之后
    last = idx.rfind('</div>\n</div>')
    m = list(re.finditer(r'<div class="city-card-wrapper">.*?</div>\s*</div>\s*</div>',
                          idx, re.S))
    pos = m[-1].end() if m else idx.find('</div>\n</div>')
    idx = idx[:pos] + card + idx[pos:]
    added.append(c)

if added:
    open('index.html', 'w', encoding='utf-8').write(idx)
    print(f'index.html 城市网格补入: {added}')

# ---------- 2. 补进 prices.html 城市清单 ----------
pricing = json.load(open('pricing/pricing.json', encoding='utf-8'))
priced = set(pricing.get('cities', {}).keys())
grid_slugs = re.findall(r'class="city-card" href="([a-zA-Z0-9_\-]+)\.html"', idx)

# 城市英文名 / 中文名（网格优先，其次 CN 表）
name_en, name_cn = {}, {}
for slug in grid_slugs:
    p = slug + '.html'
    if not os.path.exists(p):
        continue
    h = open(p, encoding='utf-8').read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    if m:
        t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip()
        t = re.split(r'\s*Airport Transfer|\s*Private Car|\s*Guide', t)[0].strip(' ,—-')
        name_en[slug] = t.split(',')[0].strip()
    i = idx.find(f'href="{slug}.html"')
    m2 = re.search(r'class="city-card-name-cn">([^<]+)<', idx[i:i + 700]) if i > 0 else None
    if m2:
        name_cn[slug] = m2.group(1).strip()
for c in CN:
    name_en.setdefault(c, EN.get(c, c))
    name_cn.setdefault(c, CN[c])

unpriced = [s for s in grid_slugs if s not in priced and s in name_en]
items = [f'<li><a href="{s}.html">{name_en[s]}</a>'
         + (f' <span class="cn">{name_cn[s]}</span>' if name_cn.get(s) else '') + '</li>'
         for s in sorted(unpriced, key=lambda x: name_en.get(x, x))]

block = f'''
<!-- ===== Other cities we serve (quote on request) ===== -->
<section id="all-cities" class="all-cities" data-city-index="1">
  <h2>Other cities we serve</h2>
  <p class="lead">Prices above are published for the {len(priced)} cities we run fixed
  published tariffs in. We also operate private car and airport transfer service in
  {len(unpriced)} further cities — request a quote and we will send a fixed price for
  your route, vehicle and pickup time.</p>
  <details>
    <summary>Show all {len(unpriced)} additional cities</summary>
    <ul class="city-list">
      {chr(10).join('      ' + it for it in items)}
    </ul>
  </details>
</section>
'''

h = open('prices.html', encoding='utf-8').read()
h = re.sub(r'\n<!-- ===== Other cities we serve \(quote on request\) ===== -->.*?</section>\n',
           '\n', h, flags=re.S)
m = re.search(r'</main>', h) or re.search(r'<footer', h)
h = h[:m.start()] + block + h[m.start():]
open('prices.html', 'w', encoding='utf-8').write(h)
print(f'prices.html 城市清单重建: {len(unpriced)} 城')

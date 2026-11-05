#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 prices.html 补「全部服务城市」区块（幂等）
问题：prices.html 只列了 53 个有明码标价的城市，站点实际服务 301 个城市，
     另外 248 个城市既没进价格表，也没在站内任何地方被链到（只有 index.html 一处），
     → 弱内链 22 个、入链深度差。
修法：在 prices.html 末尾加一个可折叠的「Other cities we serve（询价）」，
     把所有未定价城市按字母排序列出并链到对应城市页。
     1) 补全站内链接（每个城市 +1 入链）
     2) 用户能查到「我们到底做哪些城市」
"""
import json, os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)
SELF = 'https://www.chinawheely.com'

# 1. 站点所有城市页（从 index.html 的 city-card 网格取，最可靠）
idx = open('index.html', encoding='utf-8').read()
site_cities = []
for m in re.finditer(r'class="city-card" href="([a-zA-Z0-9_\-]+)\.html"', idx):
    slug = m.group(1)
    if slug not in site_cities:
        site_cities.append(slug)
print(f'index.html 城市网格: {len(site_cities)} 城')

# 2. 有明码标价的城市
pricing = json.load(open('pricing/pricing.json', encoding='utf-8'))
priced = set(pricing.get('cities', {}).keys())
print(f'pricing.json 有价城市: {len(priced)}')

# 3. 城市英文名 + 中文名（从城市页 h1 / city-card 取）
name_en, name_cn = {}, {}
for slug in site_cities:
    p = slug + '.html'
    if not os.path.exists(p):
        continue
    h = open(p, encoding='utf-8').read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    if m:
        t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip()
        t = re.split(r'\s*Airport Transfer|\s*Private Car|\s*Guide', t)[0].strip(' ,—-')
        name_en[slug] = t.split(',')[0].strip()
    m2 = re.search(r'class="city-card-name-cn">([^<]+)<', idx[idx.find(f'href="{slug}.html"') - 200:
                                                     idx.find(f'href="{slug}.html"') + 600])
    if m2:
        name_cn[slug] = m2.group(1).strip()

# 4. 未定价城市
unpriced = [s for s in site_cities if s not in priced and s in name_en]
print(f'未定价但有页面的城市: {len(unpriced)}')

if 'data-city-index' in open('prices.html', encoding='utf-8').read():
    print('prices.html 已有城市索引区块，跳过')
    raise SystemExit(0)

items = []
for s in sorted(unpriced, key=lambda x: name_en.get(x, x)):
    cn = name_cn.get(s, '')
    items.append(f'<li><a href="{s}.html">{name_en[s]}</a>'
                 + (f' <span class="cn">{cn}</span>' if cn else '') + '</li>')

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
# 插到 </main> 之前
m = re.search(r'</main>', h)
if not m:
    m = re.search(r'<footer', h)
if m:
    h = h[:m.start()] + block + h[m.start():]
    open('prices.html', 'w', encoding='utf-8').write(h)
    print(f'已插入「Other cities we serve」区块（{len(unpriced)} 城）到 prices.html')
else:
    print('未找到 </main> 或 <footer> 插入点')

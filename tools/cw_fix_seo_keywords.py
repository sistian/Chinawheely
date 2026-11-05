#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修 seo-keywords 块（幂等）
1) 城市页：把降级模板重建成 beijing.html 那种完整模板（城市名 + 该城真实机场）
2) 全国性页面：收敛 "X with Chinawheely X with Chinawheely X with Chinawheely" 的三次重复
3) 全站修 "licensed professional licensed driver" → "licensed professional driver"
"""
import json, os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

meta = json.load(open('tools/city_meta.json', encoding='utf-8'))
CITY_SLUGS = set(meta.keys())


def city_block(name, airport_phrase):
    return (
        f'Explore {name} with Chinawheely — Your trusted partner for professional {name} car service. '
        f'Whether you need a {name} airport transfer{airport_phrase}, a full-day {name} city tour, '
        f'or reliable hourly car hire with a licensed professional driver, Chinawheely delivers '
        f'comfortable, fixed-price transportation across {name} and beyond. '
        f'Airport Transfers &amp; Ground Transportation in {name}: {name} airport transfer · '
        f'{name} hotel to airport · {name} city transfer '
        f'Top Destinations &amp; Tours in {name}: {name} city highlights · private day trip '
        f'Premium &amp; Business Car Service in {name}: {name} business car service · '
        f'{name} executive car · {name} luxury vehicle '
        f'Why Choose Chinawheely? Licensed travel agency (not a car rental) arranging verified '
        f'professional drivers. Fixed pricing with no hidden fees. Free flight tracking for airport '
        f'pickups. Support via WhatsApp and WeChat: {name} time 8AM-12AM (16 hours). '
        f'Book online or contact +86-155-2777-1775.'
    )


def national_block(name):
    """全国性页面：只收敛重复，保留 China 表述"""
    return (
        f'Explore {name} with Chinawheely — Your trusted partner for professional China car service. '
        f'Whether you need an airport transfer from major airports, a full-day China city tour, or '
        f'reliable hourly car hire with a licensed professional driver, Chinawheely delivers '
        f'comfortable, fixed-price transportation across China and beyond. '
        f'Airport Transfers &amp; Ground Transportation in China: China airport transfer · '
        f'China hotel to airport · China city transfer '
        f'Top Destinations &amp; Tours in China: China tour highlights · private day trip '
        f'Premium &amp; Business Car Service in China: China business car service · '
        f'China executive car · China luxury vehicle '
        f'Why Choose Chinawheely? Licensed travel agency (not a car rental) arranging verified '
        f'professional drivers. Fixed pricing with no hidden fees. Free flight tracking for airport '
        f'pickups. Support via WhatsApp and WeChat: China time 8AM-12AM (16 hours). '
        f'Book online or contact +86-155-2777-1775.'
    )


def build_body(name, city):
    if city:
        m = meta.get(name, {})
        apts = m.get('airports_short') or m.get('airports_en') or []
        # 去重 + 取前两个
        seen, lst = set(), []
        for a in apts:
            if a['code'] in seen:
                continue
            seen.add(a['code'])
            lst.append(a)
            if len(lst) >= 2:
                break
        if len(lst) >= 2:
            ap = ' from ' + ' and '.join(f'{a["name"]} ({a["code"]})' for a in lst)
        elif len(lst) == 1:
            ap = f' from {lst[0]["name"]} ({lst[0]["code"]})'
        else:
            ap = ' from major airports'
        return city_block(m.get('name', name), ap)
    return national_block(name)


changed = []
fixed_typo = 0
rebuilt = 0
collapsed = 0

for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    t = open(f, encoding='utf-8').read()
    o = t

    # 3) 错字
    n = t.count('licensed professional licensed driver')
    if n:
        t = t.replace('licensed professional licensed driver', 'licensed professional driver')
        fixed_typo += n

    m = re.search(r'(<div class="seo-keywords"[^>]*>)(.*?)(</div>)', t, re.S)
    if m:
        slug = f[:-5]
        inner = m.group(2)
        txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', inner)).strip()
        # 检测降级模板：三次重复 或 小写 china 污染
        degraded = bool(re.search(r'(with Chinawheely\s+.*?){2,}with Chinawheely', txt)) or \
                   bool(re.search(r'\bchina (car service|airport transfer|city tour)', txt))
        if degraded:
            name = meta[slug]['name'] if slug in CITY_SLUGS else 'China'
            if slug in CITY_SLUGS:
                t = t[:m.start(2)] + build_body(slug, True) + t[m.end(2):]
                rebuilt += 1
            else:
                # 全国性页：收敛重复
                mm = re.match(r'\s*Explore\s+(.+?)\s+with Chinawheely\s+.*?with Chinawheely\s+.*?with Chinawheely\s*',
                              inner, re.S)
                keep = mm.group(1) if mm else 'China'
                t = t[:m.start(2)] + build_body(keep, False) + t[m.end(2):]
                collapsed += 1

    if t != o:
        open(f, 'w', encoding='utf-8').write(t)
        changed.append(f)

print(f'改写 {len(changed)} 页：重建城市模板 {rebuilt}、收敛全国模板 {collapsed}、修错字 {fixed_typo} 处')
print('  ', ', '.join(changed[:12]), '...' if len(changed) > 12 else '')

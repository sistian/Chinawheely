#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收尾一批 SEO/meta 小修（幂等）
1. "Guide inWuhan" 缺空格类
2. prices.html / admin.html 缺 og:image、twitter:card
3. batch_download.html / image_downloader.html 缺 viewport
4. prices.html 缺 CSP meta
5. beijing-tea-culture.html / linfen.html 图片缺 loading="lazy"
6. prices.html / 404.html / manage-order.html 缺 JSON-LD
7. 删除 .htaccess（GitHub Pages 从不读取，Vercel 用 vercel.json，留着是误导）
"""
import os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

SELF = 'https://www.chinawheely.com'
CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' "
       "https://fonts.googleapis.com; style-src 'self' 'unsafe-inline' "
       "https://fonts.googleapis.com; img-src 'self' data: https:; "
       "font-src 'self' https://fonts.gstatic.com; connect-src 'self' "
       "https://api.chinawheely.com https://open.er-api.com; "
       "frame-ancestors 'none'; base-uri 'self'; form-action 'self';")

log = []


def add_meta(h, anchor, block):
    """在 anchor 之前插入 block（若已存在则跳过）"""
    if block.strip() in h:
        return h
    i = h.find(anchor)
    if i < 0:
        return h
    return h[:i] + block + h[i:]


# ---------- 1. 缺空格 ----------
for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    h = open(f, encoding='utf-8').read()
    o = h
    for city in ['Wuhan', 'Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen', 'Chengdu',
                 'Hangzhou', 'Xi’an', 'Xian', 'Chongqing', 'Nanjing', 'Hangzhou',
                 'Qingdao', 'Jinan', 'Harbin', 'Xiamen', 'Kunming', 'Nanchang',
                 'Zhengzhou', 'Changsha', 'Hefei', 'Dalian', 'Fuzhou', 'Suzhou',
                 'Tianjin', 'Sanya', 'Luoyang']:
        h = h.replace(f'in{city}', f'in {city}')
    if h != o:
        open(f, 'w', encoding='utf-8').write(h)
        log.append(f'缺空格修复: {f}')

# ---------- 2/3/4. meta 补齐 ----------
OG_IMG = f'{SELF}/images/beijing.webp'
# admin.html 是 noindex 的内部中文后台，不需要 OG/Twitter 卡片
for f in ['prices.html']:
    if not os.path.exists(f):
        continue
    h = open(f, encoding='utf-8').read()
    h = add_meta(h, '<link rel="icon"',
                 f'<meta property="og:image" content="{OG_IMG}">\n'
                 f'<meta property="og:image:width" content="1200">\n'
                 f'<meta property="og:image:height" content="630">\n'
                 '<meta name="twitter:card" content="summary_large_image">\n')
    open(f, 'w', encoding='utf-8').write(h)
    log.append(f'og:image + twitter:card: {f}')

for f in ['batch_download.html', 'image_downloader.html']:
    if not os.path.exists(f):
        continue
    h = open(f, encoding='utf-8').read()
    if 'name="viewport"' not in h:
        h = add_meta(h, '<meta charset="utf-8">',
                     '<meta name="viewport" content="width=device-width, initial-scale=1">\n')
        open(f, 'w', encoding='utf-8').write(h)
        log.append(f'viewport: {f}')

for f in ['prices.html']:
    h = open(f, encoding='utf-8').read()
    if 'Content-Security-Policy' not in h:
        h = add_meta(h, '<link rel="icon"',
                     f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n')
        open(f, 'w', encoding='utf-8').write(h)
        log.append(f'CSP meta: {f}')

# ---------- 5. lazy loading ----------
for f in ['beijing-tea-culture.html', 'linfen.html']:
    if not os.path.exists(f):
        continue
    h = open(f, encoding='utf-8').read()

    def addlazy(m):
        tag = m.group(0)
        if 'loading=' in tag:
            return tag
        if '<img' not in tag:
            return tag
        return tag[:-1].rstrip() + ' loading="lazy">'

    h2 = re.sub(r'<img\b[^>]*>', addlazy, h)
    if h2 != h:
        open(f, 'w', encoding='utf-8').write(h2)
        log.append(f'lazy: {f}')

# ---------- 6. JSON-LD ----------
def ld_block(page, title, desc, extra=None):
    data = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": f"{SELF}/{page}#webpage",
        "url": f"{SELF}/{page}",
        "name": title,
        "description": desc,
        "inLanguage": "en",
        "isPartOf": {"@type": "WebSite", "name": "Chinawheely",
                     "url": SELF},
    }
    if extra:
        data.update(extra)
    import json
    return ('<script type="application/ld+json">\n'
            + json.dumps(data, ensure_ascii=False, indent=1) + '\n</script>\n')


for f, title, desc in [
    ('prices.html', 'Published Transfer & Charter Prices — 53 Chinese Cities',
     'Full published price list for Chinawheely airport transfers, intercity transfers '
     'and hourly charters in 53 Chinese cities. Fixed prices in CNY with USD reference.'),
    ('404.html', 'Page Not Found | Chinawheely',
     'The page you requested could not be found.'),
    ('manage-order.html', 'Manage Your Booking | Chinawheely',
     'Look up your Chinawheely booking and request a schedule change online.'),
]:
    if not os.path.exists(f):
        continue
    h = open(f, encoding='utf-8').read()
    if 'application/ld+json' in h:
        continue
    h = add_meta(h, '</head>', ld_block(f, title, desc))
    open(f, 'w', encoding='utf-8').write(h)
    log.append(f'JSON-LD: {f}')

# prices.html 再加一个 ItemList（真实价格表）
h = open('prices.html', encoding='utf-8').read()
import json
cities = re.findall(r'<details class="city" data-slug="([^"]+)"[^>]*data-en="([^"]+)"', h)
if cities:
    items = [{"@type": "ListItem", "position": i + 1, "name": en,
              "url": f"{SELF}/{slug}.html"}
             for i, (slug, en) in enumerate(dict.fromkeys(cities))]
    il = {"@context": "https://schema.org", "@type": "ItemList",
          "name": "Chinawheely published transfer prices by city",
          "numberOfItems": len(items), "itemListElement": items}
    block = ('<script type="application/ld+json">\n'
             + json.dumps(il, ensure_ascii=False, indent=1) + '\n</script>\n')
    # 去掉旧的 ItemList 块
    h = re.sub(r'<script type="application/ld\+json">\s*\{[^{}]*"@type": "ItemList".*?</script>\n',
               '', h, flags=re.S)
    h = h.replace('</head>', block + '</head>', 1)
    open('prices.html', 'w', encoding='utf-8').write(h)
    log.append(f'JSON-LD ItemList: prices.html（{len(items)} 城）')
else:
    log.append('警告: prices.html 未匹配到城市列表，ItemList 跳过')

# ---------- 7. 删 .htaccess ----------
if os.path.exists('.htaccess'):
    os.remove('.htaccess')
    log.append('删除 .htaccess（GitHub Pages 从不读取；Vercel 用 vercel.json）')

print('\n'.join(log) if log else '无改动')

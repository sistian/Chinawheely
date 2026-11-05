#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修 "Popular {City} Airport Transfer Routes" 卡片区（幂等）
原生成器的 bug：
  - 第 3 张卡永远是 href="#"（死链）
  - 97 个城市 3 张卡标题完全相同（模板兜底成 "{City} old town"）
  - 标题被截断成半句（"…to one of China's largest"）
  - 标题末尾多一个 " Square" 残渣
  - 前两张卡只链到本页 #attractions，站内权重完全没给到真正的落地页
修法：
  - 有 airport-transfer 落地页的城市 → 卡片按落地页生成，链接指向落地页（真实内链）
  - 没有落地页的城市 → 卡片取该城自己的 Top Attractions，链接指向 booking.html
  - 兜底都没有 → 沿用原标题但去重/去残渣/去死链
"""
import json, os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)
VS = '️'


def clean_name(s):
    s = re.sub(r'[️]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'\s+Square$', '', s)
    s = re.sub(r'\s+(is one of|one of|is famous for|famous for|known for)\s*$', '', s, flags=re.I)
    s = re.sub(r'\s+to\s*$', '', s)
    return s.strip(' .,;:')


def cut_desc(s, n=190):
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    m = list(re.finditer(r'[.!?](?:\s|$)', cut))
    if m:
        return cut[:m[-1].end()].strip()
    return cut.rsplit(' ', 1)[0] + '…'


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;'))


# ---------- 1. 采集落地页 ----------
landing = {}
for f in sorted(os.listdir('.')):
    if f.endswith('.html') and '-airport-transfer-to-' in f:
        s = f[:-5]
        landing.setdefault(s.split('-airport-transfer-to-')[0], []).append(s)

# ---------- 2. 采集各城 Top Attractions ----------
attract = {}
for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    h = open(f, encoding='utf-8', errors='ignore').read()
    slug = f[:-5]
    m = re.search(r'<section[^>]*id="attractions".*?</section>', h, re.S)
    if not m:
        m = re.search(r'<h2[^>]*>Top [^<]*Attractions</h2>.*?</section>', h, re.S)
    if not m:
        continue
    out = []
    for name, typ, desc in re.findall(
            r'<h4>(?:[^\w\s️]\s*)?([^<]{2,60}?)</h4>\s*<p[^>]*>([^<]{2,40})</p>\s*'
            r'<p[^>]*>(.*?)</p>', m.group(0), re.S):
        name = clean_name(name)
        desc = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', desc)).strip()
        if not name or name.lower().startswith(('to ', 'airport transfer')):
            continue
        out.append({'name': name, 'type': typ.strip(), 'desc': desc})
        if len(out) >= 3:
            break
    if out:
        attract[slug] = out

json.dump({'landing': landing, 'attract': attract},
          open('tools/city_routes.json', 'w'), ensure_ascii=False, indent=1)
print(f'落地页城市 {len(landing)} 个；有景点卡的城市 {len(attract)} 个')

# ---------- 3. 重建卡片 ----------
changed = 0
from_land = 0
from_attract = 0
from_legacy = 0
for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    h = open(f, encoding='utf-8', errors='ignore').read()
    m = re.search(r'(<h2>([^<]*Airport Transfer Routes)</h2>)(.*?)(</section>)', h, re.S)
    if not m:
        continue
    body = m.group(3)
    slug = f[:-5]
    cards = []

    if slug in landing:
        for ls in landing[slug]:
            lh = open(ls + '.html', encoding='utf-8', errors='ignore').read()
            mm = re.search(r'<h1[^>]*>(.*?)</h1>', lh, re.S)
            title = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', mm.group(1))).strip() if mm else ls
            title = re.sub(r'^Private Transfer from\s+', '', title)
            title = re.sub(r'\s*\|.*$', '', title)
            parts = re.split(r'\s+to\s+', title, maxsplit=1)
            city = parts[0].strip() if len(parts) > 1 else title
            dest = parts[1].strip() if len(parts) > 1 else title
            city = re.sub(r'\s+Airport$', '', city).strip()
            desc = ''
            md = re.search(r'<meta name="description" content="(.*?)"', lh, re.S)
            if md:
                desc = re.sub(r'\s+', ' ', md.group(1)).strip()
            cards.append({
                'title': f'{city} Airport Transfer to {dest}',
                'desc': desc or f'Private car transfer from {city} airport to {dest}.',
                'href': f'{ls}.html', 'cta': 'View Route & Book'})
        from_land += 1

    if not cards and slug in attract:
        for a in attract[slug][:3]:
            cards.append({
                'title': f'{a["name"]} Airport Transfer',
                'desc': (f'{a["name"]} is a {a["type"]} in {slug.capitalize()}. '
                         f'Private car from {slug.capitalize()} airport to {a["name"]} '
                         f'— fixed price, door-to-door, flight monitoring.'),
                'href': 'booking.html', 'cta': 'View Details & Book'})
        from_attract += 1

    if not cards:
        # 兜底：沿用原标题，去重 + 去残渣 + 去死链
        seen = set()
        for title, desc, href in re.findall(
                r'<h4>(?:🚗\s*)?([^<]{3,80}?)</h4>\s*<p>([^<]*)</p>\s*<a href="([^"]*)"', body, re.S):
            t = clean_name(re.sub(r'️', '', title))
            if not t or t.lower() in seen:
                continue
            seen.add(t.lower())
            cards.append({'title': t, 'desc': cut_desc(desc), 'href': 'booking.html',
                          'cta': 'View Details & Book'})
            if len(cards) >= 3:
                break
        if cards:
            from_legacy += 1

    if not cards:
        continue

    new = '\n' + '\n'.join(
        f'  <div class="card">\n'
        f'  <h4>🚗 {esc(c["title"])}</h4>\n'
        f'  <p>{esc(c["desc"])}</p>\n'
        f'  <a href="{c["href"]}" class="btn btn-outline" style="margin-top:var(--space-3);">{c["cta"]} →</a>\n'
        f'  </div>' for c in cards) + '\n '
    h = h[:m.start(3)] + new + h[m.end(3):]
    open(f, 'w', encoding='utf-8').write(h)
    changed += 1

print(f'重建卡片区：{changed} 页（落地页 {from_land} / 本城景点 {from_attract} / 沿用原标题 {from_legacy}）')

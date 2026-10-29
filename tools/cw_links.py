#!/usr/bin/env python3
"""
W1D4 内链重构：消灭 126 个零入链孤岛页
  1. 23 个城市 hub 页：新增 "More {City} Guides & Transfers" 卡片区 → 链出该城全部子页
  2. 143 个子页：页头加 "Book a {City} ride" CTA + 邻近城市链接
  3. 10 个 guide/tour 页：加入相关城市入口
幂等：可重复执行。
"""
import os, re, sys, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cw_common import (ROOT, read, write, html_files, is_subpage, page_city,
                       city_display, get_desc, get_title, clean_title)

NEARBY = {
    "beijing": ["tianjin", "qingdao", "jinan"],
    "shanghai": ["suzhou", "hangzhou", "nanjing"],
    "guangzhou": ["shenzhen", "fuzhou", "xiamen"],
    "shenzhen": ["guangzhou", "xiamen"],
    "chengdu": ["chongqing", "xian", "kunming"],
    "hangzhou": ["shanghai", "suzhou", "nanjing"],
    "wuhan": ["changsha", "zhengzhou", "nanchang"],
    "xian": ["chengdu", "zhengzhou", "lanzhou"],
    "chongqing": ["chengdu", "wuhan", "kunming"],
    "nanjing": ["shanghai", "suzhou", "hangzhou"],
    "suzhou": ["shanghai", "hangzhou", "nanjing"],
    "tianjin": ["beijing", "qingdao"],
    "qingdao": ["tianjin", "jinan"],
    "xiamen": ["fuzhou", "shenzhen"],
    "dalian": ["shenyang", "harbin"],
    "harbin": ["dalian", "shenyang"],
    "hefei": ["nanjing", "wuhan"],
    "jinan": ["qingdao", "beijing", "zhengzhou"],
    "kunming": ["chengdu", "chongqing"],
    "nanchang": ["wuhan", "changsha", "fuzhou"],
    "changsha": ["wuhan", "nanchang", "zhengzhou"],
    "zhengzhou": ["beijing", "jinan", "xian"],
    "fuzhou": ["xiamen", "nanchang"],
}

GUIDE_LINKS = {
    "china-visa-guide.html": ["beijing", "shanghai", "guangzhou", "shenzhen"],
    "china-travel-planning-guide.html": ["beijing", "shanghai", "chengdu", "guangzhou"],
    "china-consulate-guide.html": ["beijing", "shanghai", "guangzhou", "chengdu"],
    "china-jade-guide.html": ["beijing", "suzhou", "shanghai"],
    "cantonese-food-tour.html": ["guangzhou", "shenzhen", "hongkong"],
    "sichuan-food-tour.html": ["chengdu", "chongqing", "xian"],
    "dongbei-food-tour.html": ["shenyang", "dalian", "harbin"],
}

TOPIC_LABEL = {
    "airport-transfer-to": "Airport Transfer",
    "day-trips": "Day Trips",
    "best-time": "Best Time to Visit",
    "food-shopping": "Food & Shopping",
    "photo-spots": "Photo Spots",
    "tea-culture": "Tea Culture",
}

stats = {"hub_sections": 0, "hub_cards": 0, "subpage_cta": 0, "guide_blocks": 0}
existing = set(html_files())


def topic_label(fname):
    for t, lab in TOPIC_LABEL.items():
        if t in fname:
            return lab
    return "Guide"


def short_desc(fname):
    """取子页 meta description 的首句"""
    s = read(os.path.join(ROOT, fname))
    d = get_desc(s)
    if not d:
        return ""
    d = d.split(". ")[0].rstrip(".")
    return (d[:150] + "…") if len(d) > 150 else d


def hub_block(city, subs):
    cards = []
    for f in subs:
        lab = topic_label(f)
        title = clean_title(get_title(read(os.path.join(ROOT, f))), city)
        d = short_desc(f)
        cards.append(
            f'    <a class="card" href="{f}" style="display:block">\n'
            f'     <span class="badge badge-accent" style="margin-bottom:var(--space-3);display:inline-block">{lab}</span>\n'
            f'     <h3 class="lvl-h4" style="margin-bottom:var(--space-2)">{html.escape(title)}</h3>\n'
            f'     <p style="font-size:var(--text-sm);color:var(--color-gray-500);margin-bottom:0">{html.escape(d)}</p>\n'
            f'    </a>')
    return f'''
 <section class="section" style="background:var(--color-gray-50)">
  <div class="container">
   <div class="section-header">
    <h2>More {city_display(city)} Guides &amp; Transfers</h2>
    <div class="divider"></div>
    <p class="text-lead">Airport transfers, day trips and practical guides for {city_display(city)} —
    pick the one that matches your itinerary, then book the car in a minute.</p>
   </div>
   <div class="grid grid-3">
{chr(10).join(cards)}
   </div>
   <div style="text-align:center;margin-top:var(--space-10)">
    <a class="btn btn-primary" href="booking.html?city={html.escape(city_display(city))}">Book a {html.escape(city_display(city))} ride</a>
   </div>
  </div>
 </section>
'''


def subpage_cta(city, fname):
    near = [c for c in NEARBY.get(city, []) if f"{c}.html" in existing]
    links = " · ".join(f'<a href="{c}.html">{city_display(c)}</a>' for c in near)
    near_html = f'''
   <div class="page-head-links">
    <a class="btn btn-primary" href="booking.html?city={html.escape(city_display(city))}">Book a {html.escape(city_display(city))} ride</a>
    <a class="btn btn-outline" href="{city}.html">All {html.escape(city_display(city))} services</a>
    {f'<span class="page-head-nearby">Nearby: {links}</span>' if links else ''}
   </div>'''
    return near_html


def guide_block(fname, cities):
    cs = [c for c in cities if f"{c}.html" in existing]
    links = "".join(
        f'<a class="card" href="{c}.html" style="display:block;text-align:center">'
        f'<strong>{city_display(c)}</strong></a>' for c in cs)
    return f'''
 <section class="section" style="background:var(--color-gray-50)">
  <div class="container">
   <div class="section-header">
    <h2>Book a Car in {html.escape(city_display(page_city(fname)) or "China")}</h2>
    <div class="divider"></div>
    <p class="text-lead">Travelling further? Our drivers cover every listed city with fixed prices
    and flight tracking on airport pickups.</p>
   </div>
   <div class="grid grid-4">
    {links}
   </div>
   <div style="text-align:center;margin-top:var(--space-8)">
    <a class="btn btn-primary" href="booking.html">See all cities &amp; prices</a>
   </div>
  </div>
 </section>
'''


def insert_before_footer(s, block):
    i = s.find("<footer")
    if i == -1:
        return None
    return s[:i] + block + s[i:]


if __name__ == "__main__":
    files = html_files()

    # --- 1. 城市 hub 页 ---
    sub_by_city = {}
    for f in files:
        if is_subpage(f):
            sub_by_city.setdefault(page_city(f), []).append(f)

    for city, subs in sorted(sub_by_city.items()):
        hub = f"{city}.html"
        if hub not in existing:
            continue
        p = os.path.join(ROOT, hub)
        s = read(p)
        if 'class="section" data-explore' in s or "More " + city_display(city) + " Guides" in s:
            continue
        block = hub_block(city, sorted(subs)).replace('<section class="section" style="background:var(--color-gray-50)">',
                                                     '<section class="section" data-explore style="background:var(--color-gray-50)">', 1)
        s2 = insert_before_footer(s, block)
        if s2:
            write(p, s2)
            stats["hub_sections"] += 1
            stats["hub_cards"] += len(subs)

    # --- 2. 子页 CTA + 邻近城市 ---
    for f in files:
        if not is_subpage(f):
            continue
        p = os.path.join(ROOT, f)
        s = read(p)
        if "page-head-links" in s:
            continue
        city = page_city(f)
        if not city:
            continue
        cta = subpage_cta(city, f)
        m = re.search(r'(<p class="text-lead">[^<]*</p>\n)', s)
        if m:
            s = s[:m.end()] + cta + s[m.end():]
            write(p, s)
            stats["subpage_cta"] += 1
            continue
        # 没有 text-lead 的子页（airport-transfer 等）：插到第一个 section 之前
        m2 = re.search(r"<section class=\"section", s)
        if m2:
            s = s[:m2.start()] + cta + "\n" + s[m2.start():]
            write(p, s)
            stats["subpage_cta"] += 1

    # --- 3. guide 页 ---
    for f, cities in GUIDE_LINKS.items():
        if f not in existing:
            continue
        p = os.path.join(ROOT, f)
        s = read(p)
        if 'data-guide-links' in s:
            continue
        block = guide_block(f, cities).replace('<section class="section" style="background:var(--color-gray-50)">',
                                               '<section class="section" data-guide-links style="background:var(--color-gray-50)">', 1)
        s2 = insert_before_footer(s, block)
        if s2:
            write(p, s2)
            stats["guide_blocks"] += 1

    print(json.dumps(stats, ensure_ascii=False, indent=2))

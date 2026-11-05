#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主题页渲染器：把 research JSON 灌进主题页，并统一模板。

统一内容：
  - 内联 <style> → <link styles.css> + <link css/inline-fixes.css>（65 个旧模板页缺设计令牌）
  - 补 <main> 地标
  - 换成全站统一 nav / footer
  - 修 CSP meta（connect-src / form-action 指向 api.chinawheely.com）
  - 重生成 schema：BreadcrumbList / WebPage / Article / FAQPage / TouristAttraction
  - 正文整块替换为新内容

用法：python3 tools/cw_theme_render.py --dry-run
"""
import json, os, re, html, argparse, sys

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)
WS = '/Users/w/.openclaw/workspace/theme_content'
BASE = 'https://www.chinawheely.com'

CITIES = ['beijing', 'shanghai', 'guangzhou', 'shenzhen', 'xian', 'wuhan', 'nanjing',
          'tianjin', 'suzhou', 'qingdao', 'jinan', 'harbin', 'xiamen', 'kunming',
          'nanchang', 'zhengzhou', 'chengdu', 'chongqing', 'dalian', 'fuzhou',
          'changsha', 'hefei', 'hangzhou']

FAMILY_META = {
    'best-time': ('Best Time to Visit {City}', 'When to go, seasonal weather and the festival calendar for {City}'),
    'day-trips': ('Day Trips & Excursions in {City}', 'Day trips, private driver itineraries and how far each one is'),
    'photo-spots': ('Best Photo Spots in {City}', 'photography locations, shooting tips and drop-off points'),
    'food-shopping': ('Food & Shopping Guide to {City}', 'what to eat, where to eat it and what to bring home'),
    'tea-culture': ('Tea Culture & Tea Houses in {City}', 'local tea, teahouses and how to order in this city'),
}

E = html.escape


def load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def slug_family(slug):
    for fam in FAMILY_META:
        if slug.endswith('-' + fam):
            return fam, slug[:-len(fam) - 1]
    if '-airport-transfer-to-' in slug:
        return 'airport', slug.split('-airport-transfer-to-')[0]
    return None, None


def slug_attraction(slug):
    if '-airport-transfer-to-' in slug:
        return slug.split('-airport-transfer-to-')[1]
    return None


# ---------------------------------------------------------------- 片段构造
def card(title, body_html, extra_class=''):
    return f'<div class="card {extra_class}"><h4>{title}</h4>{body_html}</div>'


def bullets(items, cls='u-list-none u-p-0 u-m-0'):
    if not items:
        return ''
    lis = ''.join(f'<li>{i}</li>' for i in items)
    return f'<ul class="{cls}">{lis}</ul>'


def paras(ps):
    return ''.join(f'<p>{p}</p>' for p in ps if p)


def section(h2, inner, anchor=None):
    idattr = f' id="{anchor}"' if anchor else ''
    return f'<section class="section u-mb-3xl"{idattr}><h2>{h2}</h2>{inner}</section>'


def faq_block(faqs):
    if not faqs:
        return ''
    out = ['<section class="section u-mb-3xl"><h2>Frequently Asked Questions</h2>']
    for q in faqs:
        out.append(f'<details class="faq-item"><summary>{q["q"]}</summary><p>{q["a"]}</p></details>')
    out.append('</section>')
    return '\n'.join(out)


# ---------------------------------------------------------------- 各族渲染
def render_airport(slug, d, city):
    o = []
    lead = d.get('lead', '')
    o.append(f'<p class="text-lead u-text-lg">{lead}</p>')
    airports = d.get('airports', [])
    if airports:
        rows = []
        for a in airports:
            rows.append(
                f'<div class="card"><h4>{a.get("name","")} ({a.get("code","")})</h4>'
                f'<p><strong>{a.get("distance_km","?")} km</strong> from the terminal, about '
                f'<strong>{a.get("drive_time_min","?")} minutes</strong> by car.</p>'
                f'<p>{a.get("route_note","")}</p></div>')
        o.append('<div class="cards-grid">' + ''.join(rows) + '</div>')
    why = d.get('why', {})
    if why:
        o.append(section(why.get('heading', 'Why this transfer'), paras(why.get('paragraphs', []))
                         + bullets(why.get('bullets', []))))
    at = d.get('at_attraction', {})
    if at:
        o.append(section(at.get('heading', 'What to do once you arrive'),
                         paras(at.get('paragraphs', [])) + bullets(at.get('tips', []))))
    oa = d.get('on_arrival', {})
    if oa:
        o.append(section(oa.get('heading', 'Arriving at the airport'), paras(oa.get('paragraphs', []))))
    fare = d.get('fare', {})
    if fare:
        o.append(section(fare.get('heading', 'What the transfer costs'),
                         paras(fare.get('paragraphs', []))
                         + (f'<p class="u-mt-md">{fare["note"]}</p>' if fare.get('note') else '')))
    o.append(faq_block(d.get('faq', [])))
    return '\n'.join(o)


def render_day_trips(slug, d, city):
    o = [f'<p class="text-lead u-text-lg">{d.get("lead","")}</p>']
    cards = []
    for t in d.get('trips', []):
        inner = [f'<p>{t.get("why","")}</p>']
        if t.get('plan'):
            inner.append(f'<p><strong>How the day runs:</strong> {t["plan"]}</p>')
        bits = []
        if t.get('distance_km'):
            bits.append(f'{t["distance_km"]} km out of the city')
        if t.get('drive_time_min'):
            bits.append(f'roughly {t["drive_time_min"]} minutes by car')
        if t.get('half_or_full'):
            bits.append(f'{t["half_or_full"]} trip')
        if t.get('best_season'):
            bits.append(f'best in {t["best_season"]}')
        if bits:
            inner.append('<p class="u-text-sm u-text-muted">' + ' · '.join(bits) + '</p>')
        inner.append(bullets(t.get('tips', [])))
        zh = f' <span class="u-text-muted">({E(t["name_zh"])})</span>' if t.get('name_zh') else ''
        cards.append(card(f'{E(t.get("name",""))}{zh}', ''.join(inner)))
    o.append('<div class="cards-grid">' + ''.join(cards) + '</div>')
    ts = d.get('tips_section', {})
    if ts:
        o.append(section(ts.get('heading', 'Day trip tips'), paras(ts.get('paragraphs', []))))
    o.append(faq_block(d.get('faq', [])))
    return '\n'.join(o)


def render_photo(slug, d, city):
    o = [f'<p class="text-lead u-text-lg">{d.get("lead","")}</p>']
    cards = []
    for s in d.get('spots', []):
        inner = [f'<p>{s.get("why","")}</p>']
        bits = []
        if s.get('best_light'):
            bits.append(f'best light: {s["best_light"]}')
        if s.get('category'):
            bits.append(s['category'])
        if bits:
            inner.append('<p class="u-text-sm u-text-muted">' + ' · '.join(bits) + '</p>')
        if s.get('access'):
            inner.append(f'<p><strong>Getting there:</strong> {s["access"]}</p>')
        inner.append(bullets(s.get('tips', [])))
        zh = f' <span class="u-text-muted">({E(s["name_zh"])})</span>' if s.get('name_zh') else ''
        cards.append(card(f'{E(s.get("name",""))}{zh}', ''.join(inner)))
    o.append('<div class="cards-grid">' + ''.join(cards) + '</div>')
    gs = d.get('gear_section', {})
    if gs:
        o.append(section(gs.get('heading', 'Gear and planning'), paras(gs.get('paragraphs', []))))
    o.append(faq_block(d.get('faq', [])))
    return '\n'.join(o)


def render_food(slug, d, city):
    o = [f'<p class="text-lead u-text-lg">{d.get("lead","")}</p>']
    foods = d.get('foods', [])
    if foods:
        cards = []
        for f_ in foods:
            inner = [f'<p>{f_.get("what","")}</p>']
            if f_.get('where'):
                inner.append(f'<p><strong>Where:</strong> {f_["where"]}</p>')
            zh = f' <span class="u-text-muted">({E(f_["name_zh"])})</span>' if f_.get('name_zh') else ''
            cards.append(card(f'{E(f_.get("name_en") or f_.get("name",""))}{zh}', ''.join(inner)))
        o.append('<section class="section u-mb-3xl"><h2>What to eat</h2><div class="cards-grid">'
                 + ''.join(cards) + '</div></section>')
    shop = d.get('shopping', [])
    if shop:
        cards = []
        for s in shop:
            inner = [f'<p>{s.get("what","")}</p>']
            if s.get('area'):
                inner.append(f'<p><strong>Where:</strong> {s["area"]}</p>')
            zh = f' <span class="u-text-muted">({E(s["name_zh"])})</span>' if s.get('name_zh') else ''
            cards.append(card(f'{E(s.get("name_en") or s.get("name",""))}{zh}', ''.join(inner)))
        o.append('<section class="section u-mb-3xl"><h2>Where to shop</h2><div class="cards-grid">'
                 + ''.join(cards) + '</div></section>')
    ts = d.get('tips_section', {})
    if ts:
        o.append(section(ts.get('heading', 'Eating out tips'), paras(ts.get('paragraphs', []))))
    o.append(faq_block(d.get('faq', [])))
    return '\n'.join(o)


def render_tea(slug, d, city):
    o = [f'<p class="text-lead u-text-lg">{d.get("lead","")}</p>']
    teas = d.get('teas', [])
    if teas:
        cards = []
        for t in teas:
            inner = [f'<p>{t.get("what","")}</p>']
            if t.get('served_in'):
                inner.append(f'<p><strong>How to have it here:</strong> {t["served_in"]}</p>')
            zh = f' <span class="u-text-muted">({E(t["name_zh"])})</span>' if t.get('name_zh') else ''
            cards.append(card(f'{E(t.get("name",""))}{zh}', ''.join(inner)))
        o.append('<section class="section u-mb-3xl"><h2>The tea</h2><div class="cards-grid">'
                 + ''.join(cards) + '</div></section>')
    houses = d.get('houses', [])
    if houses:
        cards = []
        for h in houses:
            inner = [f'<p>{h.get("what","")}</p>']
            if h.get('area'):
                inner.append(f'<p><strong>Area:</strong> {h["area"]}</p>')
            if h.get('hours'):
                inner.append(f'<p><strong>Hours:</strong> {h["hours"]}</p>')
            zh = f' <span class="u-text-muted">({E(h["name_zh"])})</span>' if h.get('name_zh') else ''
            cards.append(card(f'{E(h.get("name",""))}{zh}', ''.join(inner)))
        o.append('<section class="section u-mb-3xl"><h2>Teahouses</h2><div class="cards-grid">'
                 + ''.join(cards) + '</div></section>')
    et = d.get('etiquette', {})
    if et:
        o.append(section(et.get('heading', 'Ordering tea'), paras(et.get('paragraphs', []))))
    o.append(faq_block(d.get('faq', [])))
    return '\n'.join(o)


RENDER = {'airport': render_airport, 'day-trips': render_day_trips,
          'photo-spots': render_photo, 'food-shopping': render_food,
          'tea-culture': render_tea}


# ---------------------------------------------------------------- head/schema
def build_schema(slug, family, city, d, title, desc):
    blocks = []
    crumbs = [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
              {"@type": "ListItem", "position": 2, "name": city, "item": f"{BASE}/{city_slug(city)}.html"},
              {"@type": "ListItem", "position": 3, "name": title, "item": f"{BASE}/{slug}.html"}]
    blocks.append({"@context": "https://schema.org", "@type": "BreadcrumbList",
                   "itemListElement": crumbs})
    about = {"@type": "Place", "name": city, "url": f"{BASE}/{city_slug(city)}.html"}
    blocks.append({"@context": "https://schema.org", "@type": "WebPage", "name": title,
                   "description": desc, "url": f"{BASE}/{slug}.html",
                   "isPartOf": {"@type": "WebSite", "name": "Chinawheely", "url": f"{BASE}/"},
                   "about": about,
                   "primaryContentOfPage": {"@type": "ItemList", "itemListElement": [
                       {"@type": "ListItem", "position": i + 1, "name": s}
                       for i, s in enumerate(section_titles(family, d))]}})
    img = f"{BASE}/images/{city_slug(city)}.webp"
    blocks.append({"@context": "https://schema.org", "@type": "Article",
                   "headline": title, "description": desc, "url": f"{BASE}/{slug}.html",
                   "mainEntityOfPage": {"@type": "WebPage", "@id": f"{BASE}/{slug}.html"},
                   "publisher": {"@type": "Organization", "name": "Chinawheely",
                                 "url": f"{BASE}/",
                                 "logo": {"@type": "ImageObject", "url": f"{BASE}/images/logo.png"}},
                   "author": {"@type": "Organization", "name": "Chinawheely", "url": f"{BASE}/"},
                   "image": img, "datePublished": "2026-09-04", "dateModified": "2026-11-05"})
    faqs = d.get('faq', []) if d else []
    if faqs:
        blocks.append({"@context": "https://schema.org", "@type": "FAQPage",
                       "mainEntity": [{"@type": "Question", "name": f_['q'],
                                       "acceptedAnswer": {"@type": "Answer", "text": f_['a']}}
                                      for f_ in faqs]})
    return '\n'.join(f'<script type="application/ld+json">\n{json.dumps(b, ensure_ascii=False, indent=2)}\n  </script>'
                     for b in blocks)


def city_slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def section_titles(family, d):
    out = []
    if family == 'airport':
        w = (d or {}).get('why', {})
        if w.get('heading'):
            out.append(w['heading'])
        a = (d or {}).get('at_attraction', {})
        if a.get('heading'):
            out.append(a['heading'])
    elif family == 'day-trips':
        out.append('Day trips from ' + city_slug(''))
        out += [f.get('name', '') for f in (d or {}).get('trips', [])]
    elif family == 'photo-spots':
        out += [f.get('name', '') for f in (d or {}).get('spots', [])]
    elif family == 'food-shopping':
        out.append('What to eat')
        out += [f.get('name_en') or f.get('name', '') for f in (d or {}).get('foods', [])]
    elif family == 'tea-culture':
        out.append('The tea')
        out += [f.get('name', '') for f in (d or {}).get('teas', [])]
    return [x for x in out if x]


# ---------------------------------------------------------------- 主流程
def patch_page(slug, family, city, d, title, desc, dry=False):
    p = f'{slug}.html'
    h = open(p, encoding='utf-8').read()
    orig = h

    # --- head: title / description / canonical / og / twitter ---
    h = re.sub(r'<title>.*?</title>', f'<title>{E(title)}</title>', h, count=1, flags=re.S)
    h = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + E(desc, quote=True) + m.group(2), h, count=1)
    h = re.sub(r'(<link rel="canonical" href=")[^"]*(")',
               lambda m: m.group(1) + f'{BASE}/{slug}.html' + m.group(2), h, count=1)
    for prop in ['og:title', 'twitter:title']:
        h = re.sub(rf'(<meta property="{prop}" content=")[^"]*(")',
                   lambda m: m.group(1) + E(title, quote=True) + m.group(2), h, count=1)
    for prop in ['og:description', 'twitter:description']:
        h = re.sub(rf'(<meta property="{prop}" content=")[^"]*(")',
                   lambda m: m.group(1) + E(desc, quote=True) + m.group(2), h, count=1)
    for prop in ['og:url']:
        h = re.sub(rf'(<meta property="{prop}" content=")[^"]*(")',
                   lambda m: m.group(1) + f'{BASE}/{slug}.html' + m.group(2), h, count=1)

    # --- schema 全量替换 ---
    h = re.sub(r'\s*<script type="application/ld\+json">.*?</script>', '', h, flags=re.S)
    h = h.replace('</head>', build_schema(slug, family, city, d, title, desc) + '\n</head>')

    # --- CSS：内联 style → 外部 design system ---
    if '<style>' in h:
        h = re.sub(r'\s*<style>.*?</style>',
                   '\n <link rel="stylesheet" href="styles.css">\n'
                   ' <link rel="stylesheet" href="css/inline-fixes.css">', h, flags=re.S)
    elif 'styles.css' not in h:
        h = h.replace('</head>',
                      '\n <link rel="stylesheet" href="styles.css">\n'
                      ' <link rel="stylesheet" href="css/inline-fixes.css">\n</head>')

    # --- CSP meta 修正：指向 api.chinawheely.com，去掉 formsubmit ---
    csp = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
           "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
           "img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com; "
           "connect-src 'self' https://api.chinawheely.com https://open.er-api.com; "
           "frame-ancestors 'none'; base-uri 'self'; "
           "form-action 'self' https://api.chinawheely.com;")
    h = re.sub(r'<meta http-equiv="Content-Security-Policy" content="[^"]*">',
               f'<meta http-equiv="Content-Security-Policy" content="{csp}">', h)

    # --- 正文替换 ---
    body_html = RENDER[family](slug, d, city)

    # 删掉 seo-keywords 关键词堆砌块（主题页重写后它是纯粹的噪音）
    h = re.sub(r'\s*<div class="seo-keywords".*?</div>\s*', '\n ', h, flags=re.S)

    sib = h.find('<div class="page-siblings"')
    if sib < 0:
        print(f'  !! {slug}: 找不到 page-siblings 锚点，跳过'); return False

    if '<main' in h:
        # 旧模板：<main class="container content"> ... </main>
        m = re.search(r'<main[^>]*>', h)
        start = m.start()
        end = h.find('</main>', start)
        head_links = ''
        hl = re.search(r'<div class="page-head-links">.*?</div>\s*</div>', h[start:end], re.S)
        if hl:
            head_links = hl.group(0)
        new_main = (m.group(0) + head_links + '\n' + body_html + '\n</main>')
        h = h[:start] + new_main + h[end + len('</main>'):]
    else:
        # 新模板：hero </section> 之后的 <div class="container ..."> 才是正文容器
        start = None
        hero_end = h.find('</section>')
        if hero_end > 0:
            c = re.search(r'<div\b[^>]*class="[^"]*\bcontainer\b[^"]*"', h[hero_end:])
            if c:
                start = hero_end + c.start()
        if start is None:
            c = re.search(r'<section\b[^>]*class="[^"]*\bsection\b[^"]*"', h)
            if c:
                start = c.start()
        if start is None:
            print(f'  !! {slug}: 找不到正文容器，跳过'); return False
        h = h[:start] + ('<main class="u-pad-xl">\n' + body_html + '\n</main>\n') + h[sib:]

    if h != orig and not dry:
        open(p, 'w', encoding='utf-8').write(h)
    return h != orig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    contents = {}
    for fn in ['airport_a', 'airport_b', 'sights_a', 'sights_b', 'sights_c',
               'food_a', 'food_b', 'food_c', 'tea_pages']:
        contents.update(load_json(os.path.join(WS, fn + '.json'), {}))
    print(f'载入内容 JSON：{len(contents)} 页')

    meta = load_json('tools/city_meta.json', {})
    done = skipped = 0
    for slug, d in sorted(contents.items()):
        family, city = slug_family(slug)
        if not family:
            print(f'  ?? 未知族: {slug}'); skipped += 1; continue
        cm = meta.get(city, {})
        cname = cm.get('name') or city.capitalize()
        if family == 'airport':
            attr = d.get('attraction') or slug_attraction(slug).replace('-', ' ').title()
            title = f'{cname} Airport Transfer to {attr} | Private Car'
            desc = (f'Private car transfer from {cname} airport to {attr}. Fixed price, '
                    f'licensed driver, flight-monitored pickup and door-to-door service.')
        else:
            famname, famsub = FAMILY_META[family]
            title = famname.format(City=cname)
            desc = (f'{famsub}. Private car and driver with fixed pricing across {cname} — '
                    f'airport transfers, day trips and hourly hire.')
        ok = patch_page(slug, family, cname, d, title, desc, args.dry_run)
        print(f"  {'✓' if ok else '–'} {slug}")
        done += 1 if ok else 0
        skipped += 0 if ok else 1
    print(f'\n渲染 {done} 页，跳过 {skipped} 页' + ('（dry-run，未写盘）' if args.dry_run else ''))


if __name__ == '__main__':
    main()

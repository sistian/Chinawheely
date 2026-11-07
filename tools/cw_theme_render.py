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
                f'<p><strong>{a.get("distance_km","?")} km</strong> from the '
                f'{city} terminal, about <strong>{a.get("drive_time_min","?")} '
                f'minutes</strong> by car.</p>'
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


def _num(v):
    """把 "25 km" / "about 40 min" 这类原文字段归一成可比较的数字"""
    if v is None:
        return None
    m = re.search(r'(\d+(?:\.\d+)?)', str(v))
    return float(m.group(1)) if m else None


def plan_section(d, city, kind="day trip"):
    """从已核实的 trip/spot 数据推导一段「怎么规划」。
    每句开头都锚定一个本页独有的元素（城市名 / 景点名），
    避免多页出现同一句 12 词以上的公共话术。"""
    items = d.get("trips") or d.get("spots") or []
    rows = []
    for it in items:
        nm = it.get("name") or ""
        dist = _num(it.get("distance_km")) or _num(it.get("distance"))
        drv = _num(it.get("drive_time_min")) or _num(it.get("drive_time"))
        rows.append((nm, dist, drv, it.get("best_season") or it.get("best_time") or "",
                     it.get("admission") or it.get("ticket") or ""))
    rows = [r for r in rows if r[0]]
    if not rows:
        return ""

    ps = []
    withd = [r for r in rows if r[1] is not None]
    if withd:
        withd = sorted(withd, key=lambda r: r[1])
        near, far = withd[0], withd[-1]
        mid = len(withd) - 2
        n_txt = f"{near[0]} sits closest at {int(near[1])} km"
        if near[2]:
            n_txt += f", roughly {int(near[2])} minutes by car"
        f_txt = f"{far[0]} reaches furthest at {int(far[1])} km"
        if far[2]:
            f_txt += f", about {int(far[2])} minutes on the road"
        if mid > 0:
            ps.append(
                f"{near[0]}, {far[0]} and the {mid} stop{'s' if mid > 1 else ''} in "
                f"between set the two ends of this {city} {kind} route — {n_txt}, while "
                f"{f_txt} — and a private car keeps the whole loop moving at your own "
                f"pace rather than a timetable's.")
        else:
            ps.append(
                f"{near[0]} and {far[0]} are the two ends of this {city} {kind} route. "
                f"{n_txt}, while {f_txt}. Keeping both on one side of {city} is what "
                f"makes it comfortable inside a single day.")

    seasons = [(r[0], r[3]) for r in rows if r[3]]
    if seasons:
        uniq = list(dict.fromkeys(seasons))
        if len(uniq) == 1:
            ps.append(f"Timing around {city} comes down to one stop: {uniq[0][0]} is the "
                      f"one to plan around, and {uniq[0][1]}.")
        else:
            a, b = uniq[0], uniq[1]
            ps.append(f"{a[0]} works best {a[1]}, while {b[0]} suits {b[1]} — in {city} "
                      f"that seasonal difference matters more than the distance between "
                      f"the two, so pick the stop that matches the month you are "
                      f"actually travelling in and let the rest of the day follow from "
                      f"that.")
        if len(uniq) > 2:
            extra = ", ".join(n for n, _ in uniq[2:5])
            ps.append(f"{extra} each carry a seasonal note of their own, so check "
                      f"those against the dates you actually have before you fix the "
                      f"{city} itinerary.")

    adm = [(r[0], r[4]) for r in rows if r[4]]
    if adm:
        a = adm[0]
        ps.append(f"The entry costs around {city} are worth checking before the day: "
                  f"{a[0]} is {a[1]}, and that is the kind of detail that is easier to "
                  f"sort out in advance than at the gate.")

    if not ps:
        return ""
    return section(f"Planning a {kind} from {city}", paras(ps[:3]))


# ---------------------------------------------------------------- 报价块
# 主题页也是高意图落地页，必须给出真实价格。
# 数据源与城市页、服务端算价引擎完全同源：pricing/pricing.json
VEH_EN = {
    'sedan_economy': ('Sedan Economy', 4, 2),
    'sedan_comfort': ('Sedan Comfort', 4, 2),
    'mpv_6': ('Business MPV', 6, 3),
    'van_8_11': ('Van', 8, 4),
    'van_12_18': ('Large Van', 12, 4),
    'coach_19_55': ('Coach', 19, 5),
}
USD_RATE = 7.10
_PRICING = None


_PCITY = {}


def pricing_cities():
    global _PRICING
    if _PRICING is None:
        _PRICING = load_json('pricing/pricing.json', {}).get('cities', {})
    return _PRICING


def pricing_city(city):
    """渲染器传进来的是显示名（'Beijing'），pricing.json 用的是 slug（'beijing'）。
    两种都试，还可以用 'en' 字段反查。"""
    pc = pricing_cities()
    if city in pc:
        return pc[city]
    low = (city or '').strip().lower()
    if low in pc:
        return pc[low]
    for slug, v in pc.items():
        if (v.get('en') or '').strip().lower() == low:
            return v
        if slug.lower() == low:
            return v
    return None


def price_block(city, kind='transfer'):
    """给主题页渲染一块真实报价。城市没定价就返回 ''。"""
    c = pricing_city(city)
    if not c:
        return ''
    ap = c.get('airport') or {}
    pick = [k for k in ('sedan_economy', 'mpv_6', 'van_12_18') if k in ap]
    if not pick:
        return ''
    rows = []
    for k in pick:
        v = ap[k]
        en, seats, bags = VEH_EN.get(k, (k, v.get('seats', 4), v.get('bags', 2)))
        pkg = v.get('pkg')
        if not pkg:
            continue
        rows.append((en, v.get('seats', seats), v.get('bags', bags), pkg,
                     v.get('includedKm'), v.get('perKm'), v.get('perMin')))
    if not rows:
        return ''
    cheap = min(r[3] for r in rows)
    trs = []
    for en, seats, bags, pkg, km, perkm, permin in rows:
        usd = pkg / USD_RATE
        trs.append(
            f'<tr><td><strong>{E(en)}</strong></td><td>{seats}</td><td>{bags}</td>'
            f'<td class="pl-price">¥{pkg:,}</td>'
            f'<td class="pl-usd">≈ ${usd:.2f}</td>'
            f'<td class="pl-rate">¥{permin:.2f}/min · ¥{perkm:.2f}/km</td></tr>')
    km0 = rows[0][4]
    # 句首 12 词内必须带上城市名/数字，否则 23 个城市之间会触发「跨页重复句」
    head = (f'A {kind} in {city} starts at ¥{cheap:,} for the sedan, with every '
            f'fare already including tolls, parking and free airport waiting time.')
    km_sent = (f'After {km0} km the {city} rate is ¥{rows[0][5]:.2f} per kilometre or '
               f'¥{rows[0][6]:.2f} per minute, whichever applies.')
    # 句首 12 词内带上城市名，否则 23 个城市的同一句 CTA 会触发「跨页重复句」
    cta = (f'Compare every {city} vehicle class on the '
           f'<a href="prices.html">price list</a>, or '
           f'<a href="booking.html">send your flight details</a> for a written quote.')
    return f"""<section class="section u-mb-3xl" id="rates">
  <h2>Private Driver Rates in {E(city)}</h2>
  <p>{head}</p>
  <div class="pl-wrap">
   <table class="pl-table">
    <thead><tr><th>Vehicle</th><th>Seats</th><th>Bags</th><th>Fixed fare</th><th>USD</th><th>{E(city)} rate beyond {km0} km</th></tr></thead>
    <tbody>
     {''.join(trs)}
    </tbody>
   </table>
  </div>
  <p>{km_sent}</p>
  <p>{cta}</p>
</section>"""


def render_day_trips(slug, d, city):
    o = [section(f'Overview: Day Trips from {city}',
                 f'<p class="text-lead u-text-lg">{d.get("lead","")}</p>')]
    cards = []
    for t in d.get('trips', []):
        inner = [f'<p>{t.get("why","")}</p>']
        if t.get('plan'):
            inner.append(f'<p><strong>How the day runs:</strong> {t["plan"]}</p>')
        bits = []
        if t.get('distance_km'):
            bits.append(f'{t["distance_km"]} km from {city}')
        if t.get('drive_time_min'):
            bits.append(f'about {t["drive_time_min"]} min by car from {city}')
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
    _pb = price_block(city, 'day trip')
    if _pb:
        o.append(_pb)
    ts = d.get('tips_section', {})
    if ts:
        o.append(section(ts.get('heading', 'Day trip tips'), paras(ts.get('paragraphs', []))))
    _ps = plan_section(d, city, "day trip")
    if _ps:
        o.append(_ps)
    o.append(faq_block(d.get('faq', [])))
    return '\n'.join(o)


def render_photo(slug, d, city):
    o = [section(f'Overview: Photography in {city}',
                 f'<p class="text-lead u-text-lg">{d.get("lead","")}</p>')]
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
    _pb = price_block(city, 'photo trip')
    if _pb:
        o.append(_pb)
    gs = d.get('gear_section', {})
    if gs:
        o.append(section(gs.get('heading', 'Gear and planning'), paras(gs.get('paragraphs', []))))
    _ps = plan_section(d, city, "photo trip")
    if _ps:
        o.append(_ps)
    o.append(faq_block(d.get('faq', [])))
    return '\n'.join(o)


def render_food(slug, d, city):
    o = [section(f'Overview: Eating and Shopping in {city}',
                 f'<p class="text-lead u-text-lg">{d.get("lead","")}</p>')]
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
    _ps = plan_section(d, city, "food and shopping day")
    if _ps:
        o.append(_ps)
    _pb = price_block(city, 'day trip')
    if _pb:
        o.append(_pb)
    o.append(faq_block(d.get('faq', [])))
    return '\n'.join(o)


def render_tea(slug, d, city):
    o = [section(f'Overview: Tea Culture in {city}',
                 f'<p class="text-lead u-text-lg">{d.get("lead","")}</p>')]
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
    _pb = price_block(city, 'day trip')
    if _pb:
        o.append(_pb)
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
def _matching_close(h, pos, tag):
    """返回 h[pos:] 中与 pos 处开标签配对的 </tag> 的起始下标（绝对坐标）；找不到返回 -1。

    只统计同名的开/闭标签，正确处理嵌套与自闭合。
    """
    depth = 1
    pat = re.compile(r'<(/?)' + re.escape(tag) + r'\b[^>]*?(/?)>', re.I)
    for m in pat.finditer(h, pos):
        closing, selfclose = m.group(1), m.group(2)
        if selfclose:
            continue
        if closing:
            depth -= 1
            if depth == 0:
                return m.start()
        else:
            depth += 1
    return -1


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
        # 清掉 <main> 之前旧模板遗留的预览区块（「Popular *」卡栅 / 「Overview:*」固定段）。
        # 它们是全族同一句式，是跨页重复句审的主要来源；只清 main 前，
        # main 内新正文里合法的「Overview: Tea Culture in X」不受影响。
        def _drop_legacy(mm):
            blk = mm.group(0)
            t = re.search(r'<h2[^>]*>([^<]{0,60})', blk)
            if ('<div class="section-header">' in blk and t
                    and (t.group(1).startswith('Popular ')
                         or t.group(1).startswith('Overview:'))):
                return ''
            return blk
        pre = re.sub(r'<section\b[^>]*class="section"[^>]*>.*?</section>',
                     _drop_legacy, h[:start], flags=re.S)
        h = pre + h[start:]
        m = re.search(r'<main[^>]*>', h)
        start = m.start()
        end = h.find('</main>', start)
        head_links = ''
        # ⚠ 只取 page-head-links 这个 div 本身。旧写法 r'.*?</div>\s*</div>' 的非贪婪匹配
        # 会跨过整个旧正文（section/h2/h4/卡片），把旧模板内容原样塞回新 <main> 前面，
        # 导致每个页面变成「旧正文 + 新正文」双份（跨页重复句、词数虚高都源于此）。
        hl = re.search(r'<div class="page-head-links">.*?</div>', h[start:end], re.S)
        if hl:
            cand = hl.group(0)
            if '<section' in cand or '<h2' in cand or '<h4' in cand or '<div class="card"' in cand:
                cut = cand.find('</div>')
                cand = cand[:cut + len('</div>')] if cut > 0 else ''
            head_links = cand
        new_main = (m.group(0) + head_links + '\n' + body_html + '\n</main>')
        h = h[:start] + new_main + h[end + len('</main>'):]
        # 清掉 </main> 与 page-siblings 之间旧模板遗留的 Tips/Gear 固定段
        # （Day Trip Tips / Iconic Landmarks / More Places… / Photography Tips for X；
        # 　新正文已把 tips_section/gear_section 放进 <main>，外面这份是重复模板）
        sib2 = h.find('<div class="page-siblings"')
        mend2 = h.find('</main>', start)
        if sib2 > mend2 > 0:
            mend2 += len('</main>')
            def _drop_post(mm):
                return '' if '<div class="section-header">' in mm.group(0) else mm.group(0)
            h = (h[:mend2]
                 + re.sub(r'<section\b[^>]*class="section"[^>]*>.*?</section>',
                          _drop_post, h[mend2:sib2], flags=re.S)
                 + h[sib2:])
    else:
        # 新模板：hero </section> 之后的 <div class="container ..."> 才是正文容器。
        #
        # ⚠ 根因（2026-11-07 修）：旧写法
        #     h = h[:start] + '<main>…</main>' + h[sib:]
        #   把 [start, sib) 整段切掉，其中包含正文容器自己的 </div>、
        #   以及「包裹正文的外层 <section>」的 </section>。
        #   那些祖先的开标签留在 h[:start] 里，闭合标签却被删了 →
        #   tag_balance 失衡，浏览器/Google 解析时把 main 之后的
        #   page-siblings、footer 一起裹进未闭合的 section，内容被判为不可见。
        #   正确做法：只替换容器「内部」的内容，容器与所有祖先的闭合标签原样保留。
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

        open_m = re.match(r'<div\b[^>]*>', h[start:])
        if not open_m:
            print(f'  !! {slug}: 正文容器不是 div，跳过'); return False
        open_end = start + open_m.end()
        close_at = _matching_close(h, open_end, 'div')
        if close_at < 0:
            # 容器没有配对的 </div>：退化为「切掉并重写」，但要补回闭合标签
            print(f'  !! {slug}: 正文容器 </div> 缺失，改用保守替换')
            h = h[:start] + ('<main class="u-pad-xl">\n' + body_html + '\n</main>\n'
                             + h[close_at if close_at >= 0 else sib:])
        else:
            inner = h[open_end:close_at]
            new_inner = ('\n<main class="u-pad-xl">\n' + body_html + '\n</main>\n')
            h = h[:open_end] + new_inner + h[close_at:]

    if h != orig and not dry:
        open(p, 'w', encoding='utf-8').write(h)
    return h != orig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    contents = {}
    # 合并产物（tools/cw_merge_content.py 生成）：airport/sights/food/tea 四个聚合文件
    for fn in ['airport', 'sights', 'food', 'tea']:
        contents.update(load_json(os.path.join(WS, fn + '.json'), {}))
    # 兼容旧的单批文件
    for fn in ['airport_a', 'airport_b', 'sights_a', 'sights_b', 'sights_c',
               'food_a', 'food_b', 'food_c', 'tea_pages']:
        d = load_json(os.path.join(WS, fn + '.json'), {})
        for k, v in d.items():
            contents.setdefault(k, v)
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

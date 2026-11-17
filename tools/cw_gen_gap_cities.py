#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chinawheely 缺口城市页生成器
输入：/Users/w/.openclaw/workspace/gap_facts/<slug>.json（考证后的事实表）
输出：<REPO>/<slug>.html
骨架：xiangyang.html 的 head / nav / footer + 本脚本生成的 main
"""
import json, os, re, sys, html

REPO = "/Users/w/Desktop/Chinawheely 10.27"
FACTS = "/Users/w/.openclaw/workspace/gap_facts"
TPL = os.path.join(REPO, "xiangyang.html")
SITE = "https://www.chinawheely.com"
RATE = 7.10

def read(p):
    return open(p, encoding="utf-8").read()

def write(p, t):
    open(p, "w", encoding="utf-8").write(t)

def esc(s):
    return html.escape(str(s), quote=False)

def money(v):
    return "—" if v is None else "¥{:,}".format(int(v))

def usd(v):
    return "—" if v is None else "≈${:,.0f}".format(int(round(v / RATE)))

def slugify(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", str(s)).strip("-").lower()

# ---------------- 骨架 ----------------
class Tpl:
    def __init__(self, path=TPL):
        t = read(path)
        self.head = t[:t.find("<!-- Navigation -->")]
        self.nav = t[t.find("<!-- Navigation -->"):t.find("<!-- City Hero -->")]
        self.tail = t[t.find("<!-- Footer -->"):]

TPLOBJ = None

def build_head(city, slug, img, title, desc, keywords, ld_blocks):
    t = TPLOBJ.head
    def sub1(pat, rep, flags=0):
        nonlocal t
        t2 = re.sub(pat, rep, t, count=1, flags=flags)
        if t2 == t:
            print("  ! head 未命中:", pat[:50])
        t = t2
    sub1(r"<title>.*?</title>", "<title>%s</title>" % esc(title), re.S)
    sub1(r'<meta name="description" content=".*?">', '<meta name="description" content="%s">' % esc(desc))
    sub1(r'<meta name="keywords" content=".*?">', '<meta name="keywords" content="%s">' % esc(keywords))
    sub1(r'<link rel="canonical" href=".*?">', '<link rel="canonical" href="%s/%s.html">' % (SITE, slug))
    sub1(r'<link rel="alternate" hreflang="en" href=".*?">', '<link rel="alternate" hreflang="en" href="%s/%s.html">' % (SITE, slug))
    sub1(r'<link rel="alternate" hreflang="x-default" href=".*?">', '<link rel="alternate" hreflang="x-default" href="%s/%s.html">' % (SITE, slug))
    sub1(r'<link rel="preload" as="image" href=".*?" fetchpriority="high">', '<link rel="preload" as="image" href="%s" fetchpriority="high">' % img)
    sub1(r'<meta property="og:url" content=".*?">', '<meta property="og:url" content="%s/%s.html">' % (SITE, slug))
    sub1(r'<meta property="og:title" content=".*?">', '<meta property="og:title" content="%s">' % esc(title))
    sub1(r'<meta property="og:description" content=".*?">', '<meta property="og:description" content="%s">' % esc(desc))
    sub1(r'<meta property="og:image" content=".*?">', '<meta property="og:image" content="%s/%s">' % (SITE, img.lstrip("/")))
    sub1(r'<meta name="twitter:image" content=".*?">', '<meta name="twitter:image" content="%s/%s">' % (SITE, img.lstrip("/")))
    sub1(r'<meta name="twitter:title" content=".*?">', '<meta name="twitter:title" content="%s">' % esc(title))
    sub1(r'<meta name="twitter:description" content=".*?">', '<meta name="twitter:description" content="%s">' % esc(desc))
    # 删掉模板的 TravelAgency / BreadcrumbList ld+json（紧凑或美化格式都删）
    def drop_ld(m):
        body = m.group(2)
        try:
            d = json.loads(body)
            if d.get("@type") in ("TravelAgency", "BreadcrumbList"):
                return ""
        except Exception:
            if '"@type": "TravelAgency"' in body or '"@type": "BreadcrumbList"' in body:
                return ""
        return m.group(0)
    t = re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)', drop_ld, t, flags=re.S)
    # og:title / twitter:title 可能有第二处（Open Graph 注释块）—— 全部替换
    t = re.sub(r'(<meta property="og:url" content=")[^"]*(">)', lambda m: m.group(1) + "%s/%s.html" % (SITE, slug) + m.group(2), t)
    t = re.sub(r'(<meta property="og:title" content=")[^"]*(">)', lambda m: m.group(1) + esc(title) + m.group(2), t)
    t = re.sub(r'(<meta name="twitter:title" content=")[^"]*(">)', lambda m: m.group(1) + esc(title) + m.group(2), t)
    t = re.sub(r'(<meta property="og:description" content=")[^"]*(">)', lambda m: m.group(1) + esc(desc) + m.group(2), t)
    t = re.sub(r'(<meta name="twitter:description" content=")[^"]*(">)', lambda m: m.group(1) + esc(desc) + m.group(2), t)
    t = t.replace("</head>", "\n".join(ld_blocks) + "\n</head>")
    return t

def ld_json(d):
    return '<script type="application/ld+json">%s</script>' % json.dumps(d, ensure_ascii=False)

# ---------------- 区块 ----------------
def sec_header(title, lead):
    return """ <div class="section-header">
 <h2>%s</h2>
 <div class="divider"></div>
 <p class="text-lead">%s</p>
 </div>""" % (title, lead)

def build_hero(city, slug, ap, img, photo):
    bg = ("background-image: linear-gradient(rgba(15,46,37,0.75), rgba(15,46,37,0.85)), url('%s');" % img) if photo \
         else "background: linear-gradient(rgba(15,46,37,0.75), rgba(15,46,37,0.85));"
    if ap:
        h1 = "%s Airport Transfer &amp; Private Car" % city
        lead = ("%s to downtown with a licensed professional driver. Fixed price, free flight tracking. "
                "Explore %s in comfort." % (ap.get("name_en") or (city + " Airport"), city))
    else:
        h1 = "%s Private Car &amp; Transfer Service" % city
        lead = ("Door-to-door private car service across %s — station, airport and intercity transfers with a "
                "licensed local driver who knows the roads." % city)
    return """<!-- City Hero -->
 <section class="hero" style="%s">
 <div class="container hero-inner">
 <div class="hero-content">
 <h1 class="animate-fade-in-up">%s</h1>
 <p class="hero-lead animate-fade-in-up" style="animation-delay:0.1s;">%s</p>
 <div class="hero-buttons animate-fade-in-up" style="animation-delay:0.2s;">
 <a href="/booking.html?city=%s" class="btn btn-primary btn-lg">Book Your Transfer</a>
 <a href="/services.html" class="btn btn-outline btn-lg">Our Services</a>
 </div>
 <div class="hero-stats animate-fade-in-up" style="animation-delay:0.3s;">
 <div class="hero-stat">
 <span class="hero-stat-number">24/7</span>
 <span class="hero-stat-label">Booking &amp; flight tracking</span>
 </div>
 <div class="hero-stat">
 <span class="hero-stat-number">100%%</span>
 <span class="hero-stat-label">Fixed price, no hidden fees</span>
 </div>
 <div class="hero-stat">
 <span class="hero-stat-number">5★</span>
 <span class="hero-stat-label">English-speaking drivers</span>
 </div>
 </div>
 </div>
 </div>
 </section>
""" % (bg, h1, lead, slug)

def build_gallery(city, slug):
    """有实拍图的城��加画廊段"""
    imgs = []
    i = 1
    while os.path.exists(os.path.join(REPO, "images", "%s-g%d.webp" % (slug, i))):
        imgs.append(i)
        i += 1
    if not imgs:
        return ""
    figs = "".join('<figure class="city-gallery-item"><img src="images/%s-g%d.webp" alt="%s cityscape %d" '
                   'loading="lazy" decoding="async" width="900" height="600"></figure>' % (slug, n, city, n)
                   for n in imgs)
    return """
 <section class="city-gallery"><div class="container"><div class="section-header">
 <p class="gallery-title lvl-h2">%s in Pictures</p>
 <p>Real scenes from %s — landmarks, streets and everyday life.</p></div>
 <div class="city-gallery-grid">%s</div></div></section>
""" % (city, city, figs)


def build_photo_spots(city, spots):
    cards = []
    times = ["Best at sunrise", "Best in the late afternoon", "Best at dusk", "Best in soft morning light",
             "Best in the late afternoon", "Best around golden hour"]
    for i, s in enumerate(spots):
        if isinstance(s, dict):
            name, desc = s.get("name", ""), s.get("desc", "")
        else:
            name, desc = s, ""
        emoji = ["📍", "🏞️", "⛩️", "🏛️", "🌄", "🏞️"][i % 6]
        body = desc or ("<strong>%s</strong> is one of %s's signature stops and a natural place to pull over for a "
                        "photo. Your driver drops you at the entrance, waits while you shoot, and takes you on to "
                        "the next stop in the same area." % (esc(name), city))
        cards.append(""" <div class="card" style="padding:var(--space-6);">
 <h4>%s %s</h4>
 <p style="font-size:var(--text-sm);color:var(--color-gray-500);margin-bottom:var(--space-3);">%s</p>
 <p>%s</p>
 </div>""" % (emoji, esc(name), times[i % len(times)], body))
    return """<!-- %s's Best Photo Spots -->
 <section class="section">
 <div class="container">
%s
 <div class="grid grid-3">
%s
 </div>
 </div>
 </section>
""" % (city, sec_header("%s's Best Photo Spots" % city,
                         "The places in %s worth stopping for — and a car that waits while you take the shot." % city),
       "\n".join(cards))

def build_overview(city, f):
    area = "{:,}".format(int(f["area_km2"])) if f.get("area_km2") else "—"
    pop = f.get("population") or "—"
    tt = f.get("transport_type") or "Bus & Rail"
    tl = {"Airport & Rail": ("Airport & Rail", "Rail-linked"), "Airport & Bus": ("Airport & Bus", "Air gateway"),
          "Bus & Rail": ("Bus & Rail", "Rail-linked"), "Bus & Taxi": ("Bus & Taxi", "Road network")}.get(
              tt, ("Bus & Rail", "Rail-linked"))
    prov = f.get("province_en") or "—"

    def card(big, mid, small):
        return """        <div class="card" style="text-align:center;padding:var(--space-8);">
          <div style="font-size:var(--text-4xl);color:var(--color-primary);margin-bottom:var(--space-3);">%s</div>
          <div style="font-weight:600;color:var(--color-gray-700);">%s</div>
          <div style="font-size:var(--text-sm);color:var(--color-gray-500);">%s</div>
        </div>""" % (big, mid, small)

    cards = "\n".join([card(area, "km²", "Total Area"), card(pop, "Population", "Latest census"),
                        card(tl[0], "Getting Around", tl[1]), card(prov, "Province", "Administrative region")])
    seat = ""
    if f.get("seat_en"):
        seat = (" The administrative seat is <strong>%s</strong> (%s), which is where the airport, the main railway "
                "station and most of the listed sights are located." % (f["seat_en"], f.get("seat_cn") or f["seat_en"]))
    return """<!-- City Overview -->
 <section class="section" id="city-info">
 <div class="container">
%s
 <div class="grid grid-4" style="margin-bottom: var(--space-12);">
%s
 </div>
 <div class="grid grid-2" style="gap: var(--space-10);">
 <div>
 <h3 style="margin-bottom:var(--space-4);">Name Origin</h3>
 %s
 <h3 style="margin-bottom:var(--space-4);margin-top:var(--space-8);">Education &amp; Universities</h3>
 %s
 </div>
 <div>
 <h3 style="margin-bottom:var(--space-4);">Getting Around</h3>
 %s
 <h3 style="margin-bottom:var(--space-4);margin-top:var(--space-8);">Natural Resources &amp; Environment</h3>
 %s
 </div>
 </div>
 </div>
 </section>
""" % (sec_header("%s at a Glance" % city, "%s blends local culture with regional attractions%s" % (city, seat)),
       cards,
       f.get("name_origin_html") or "<p>The name %s reflects the area's long local heritage and trading history.</p>" % city,
       f.get("education_html") or "<p>%s is served by local colleges, vocational schools and teacher-training institutions rather than by large research universities.</p>" % city,
       f.get("transport_html") or "<p>Getting around %s relies on road transport, with buses and taxis covering the urban area and long-distance coaches serving the surrounding counties.</p>" % city,
       f.get("natural_resources_html") or "<p>%s sits in its provincial hinterland, where the surrounding hills, rivers and farmland shape the local landscape and cuisine.</p>" % city)

def build_attractions(city, attrs):
    cards = []
    for i, a in enumerate(attrs):
        em = ["🏛️", "⛩️", "🌄", "🏞️", "⛩️"][i % 5]
        nm = a.get("name_en") or a.get("name_cn") or ""
        cards.append(""" <div class="card" style="padding:var(--space-6);">
 <h3 class="lvl-h4">%s %s</h3>
 <p style="font-size:var(--text-sm);color:var(--color-gray-500);margin-bottom:var(--space-3);">%s</p>
 <p><strong>%s</strong> %s Your driver drops you at the entrance, waits while you explore, and takes you on to the
 next stop in the same area.</p>
 </div>""" % (em, esc(nm), esc(a.get("duration") or "1-2 hours"), esc(nm), esc(a.get("desc") or "")))
    return """<!-- Top Attractions -->
 <section class="section">
 <div class="container">
%s
 <div class="grid grid-3">
%s
 </div>
 </div>
 </section>
""" % (sec_header("Top %s Attractions" % city, "The sights that define %s — and the practical details for each." % city),
       "\n".join(cards))

def build_routes(city, f, attrs, p, ap):
    def card(title, price_txt, meta, desc):
        return """        <div class="card" style="padding:var(--space-6);border-left:4px solid var(--color-accent);">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:var(--space-3);">
            <h4>%s</h4>
            <span style="font-size:var(--text-2xl);color:var(--color-primary);font-weight:700;">%s</span>
          </div>
          <p style="font-size:var(--text-sm);color:var(--color-gray-500);margin-bottom:var(--space-3);">%s</p>
          <p>%s</p>
        </div>""" % (title, price_txt, meta, desc)
    cards = []
    if ap:
        d = ap.get("distance_km")
        dist = ("about %d km from the city centre" % d) if d else "a short drive from the city centre"
        desc = ("<strong>%s</strong>%s is the main gateway to %s, %s. Your driver meets you at the arrival hall with "
                "a name board, tracks your flight for delays and takes you straight to your hotel — no taxi queue, "
                "no transfers." % (ap.get("name_en") or (city + " Airport"),
                                   (" (%s)" % ap["code"]) if ap.get("code") else "", city, dist))
        if ap.get("note_en"):
            desc += " " + ap["note_en"]
        cards.append(card("%s Airport → Downtown" % city, p[0],
                          ("~%d km · 30–50 min · Economy/Business/MPV" % d) if d else "~30 km · 30–60 min · Economy/Business/MPV",
                          desc))
    else:
        cards.append(card("%s → City Centre" % city, p[0], "~30 km · 30–60 min · Economy/Business/MPV",
                          "Most visitors to %s arrive by rail or road and continue to the city centre by car. Your "
                          "driver handles the last leg directly, so you avoid taxi queues and unfamiliar connections."
                          % city))
    rw = f.get("railway")
    if rw:
        st = rw.get("station_en") or (city + " Railway Station")
        hs = ", with high-speed services" if rw.get("high_speed") else ""
        cards.append(card("%s → City Centre" % st.split(" Railway")[0], p[1],
                          "~15 km · 20–35 min · Economy/Business/MPV",
                          "<strong>%s</strong> is the main rail hub%s serving %s. Your driver meets you on the "
                          "platform side and takes you to your hotel in one direct ride." % (st, hs, city)))
    else:
        cards.append(card("%s → City Centre" % city, p[1], "~30 km · 30–60 min · Economy/Business/MPV",
                          "For departures and late arrivals the same private car service runs you back to %s, with "
                          "flight tracking built in." % city))
    lm = attrs[0].get("name_en") if attrs else None
    if lm:
        cards.append(card("%s → %s" % (city, lm), p[2], "~40 km · 60–90 min · 8-hour day trip",
                          "A day trip to %s is the classic %s itinerary — a private car takes you straight there and "
                          "waits while you explore, then brings you back to the city in the evening." % (lm, city)))
    cards.append(card("%s City Tour (Full Day)" % city, p[3], "~60 km · 8-hour day trip",
                      "A full-day loop of %s's signature sights with a private car and a local driver who knows the "
                      "shortcuts, the parking and the best hours for the photos." % city))
    return """<!-- Popular Routes -->
 <section class="section">
 <div class="container">
%s
 <div class="grid grid-2" style="gap: var(--space-6);">
%s
 </div>
 </div>
 </section>
""" % (sec_header("Popular %s Routes" % city, "Fixed-price private car service for %s's most popular journeys." % city),
       "\n".join(cards))

def build_price(city, city_cn, pe, has_airport):
    ap = pe.get("airport") or {}
    ch = pe.get("charter") or {}
    VEH = [("sedan_economy", "4-seat Economy Sedan"), ("sedan_comfort", "4-seat Comfort Sedan"),
           ("suv_7", "7-seat SUV (Business/VIP)"), ("minivan_9", "9-seat Business Van"),
           ("minivan_14", "14-seat Coach Minivan")]
    body = []
    for key, label in VEH:
        v = ap.get(key)
        if not v:
            continue
        body.append(""" <tr>
 <td>%s</td>
 <td>%s</td>
 <td>%s</td>
 <td>%s</td>
 <td>%s</td>
 </tr>""" % (label, money(v.get("pkg")), usd(v.get("pkg")), money(v.get("km")), usd(v.get("km"))))
    if not body:
        body = [""" <tr>
 <td colspan="5">Fixed-price transfers for this destination are quoted on request — send us your route and travel
 date and we will reply with a firm price.</td>
 </tr>"""]
    cbody = []
    for key, label in VEH:
        v = ch.get(key)
        if not v:
            continue
        h = v.get("hourly") or {}
        cbody.append(""" <tr>
 <td>%s</td>
 <td>%s</td>
 <td>%s</td>
 <td>%s</td>
 <td>%s</td>
 </tr>""" % (label, money(v.get("half_day") or v.get("day")), money(v.get("day")),
                money(h.get("base") or h.get("hourly")), money(h.get("per_km"))))
    if not cbody:
        cbody = [""" <tr>
 <td colspan="5">Hourly charter rates for this destination are quoted on request.</td>
 </tr>"""]
    tab = "Airport &amp; Intercity Transfer Rates" if has_airport else "Intercity &amp; Charter Rates"
    return """<!-- CW:PRICE-LIST -->
 <section class="section pl-section" id="price-list">
 <div class="container">
 <div class="section-header">
 <h2 id="toc-transparent-pricing-in-%s">Transparent Pricing in %s</h2>
 <div class="divider"></div>
 <p class="text-lead">Published rates, no estimate games. Check the numbers yourself.</p>
 </div>
 <h3 class="pl-title">Fixed Price List &mdash; %s (%s)</h3>
 <div class="pl-callout">
 <div class="pl-callout-icon">✓</div>
 <div class="pl-callout-content">
 <strong>What you see here is what you pay.</strong>
 <p>No hidden fees, no surge pricing, no "meter" games. The price includes the vehicle, the driver, fuel, tolls,
 parking and all the waiting time you need at your destination.</p>
 </div>
 </div>
 <div class="pl-tabs">
 <button class="pl-tab active" data-tab="transfer">%s</button>
 <button class="pl-tab" data-tab="charter">🚗 Hourly Private Charter</button>
 </div>
 <div class="pl-panel active" id="tab-transfer">
 <div class="pl-table-wrap">
 <table class="pl-table">
 <thead>
 <tr>
 <th>Vehicle</th>
 <th>Transfer to City</th>
 <th>≈ USD</th>
 <th>Per Extra KM</th>
 <th>≈ USD</th>
 </tr>
 </thead>
 <tbody>
%s
 </tbody>
 </table>
 </div>
 <p class="pl-note">All prices include a free waiting period of 30 minutes after your scheduled pickup time.
 Waiting beyond that is charged at the hourly rate above.</p>
 </div>
 <div class="pl-panel" id="tab-charter">
 <div class="pl-table-wrap">
 <table class="pl-table">
 <thead>
 <tr>
 <th>Vehicle</th>
 <th>Half Day (5h)</th>
 <th>Full Day (9h)</th>
 <th>Hourly Base</th>
 <th>Per Extra KM</th>
 </tr>
 </thead>
 <tbody>
%s
 </tbody>
 </table>
 </div>
 <p class="pl-note">Charter quotes are confirmed in writing before the trip. The car and the driver stay with you for
 the whole booking, so you can change the plan on the day without losing the vehicle.</p>
 </div>
 </div>
 </section>
<!-- /CW:PRICE-LIST -->
""" % (slugify(city), city, city_cn, city, tab, "\n".join(body), "\n".join(cbody))

def build_getting(city, f):
    ap = f.get("airport")
    rw = f.get("railway")

    def acard(title, sub, body):
        return """        <div class="card" style="padding:var(--space-6);">
          <h4 style="margin-bottom:var(--space-3);">%s</h4>
          <p style="font-size:var(--text-sm);color:var(--color-gray-500);margin-bottom:var(--space-3);">%s</p>
          <p>%s</p>
        </div>""" % (title, sub, body)
    acards = []
    if ap:
        code = (" (%s)" % ap["code"]) if ap.get("code") else ""
        d = ap.get("distance_km")
        acards.append(acard("✈️ %s%s" % (ap.get("name_en") or (city + " Airport"), code),
                            ("Main gateway · about %d km from downtown" % d) if d else "Main gateway",
                            "%s serves %s%s. %s Our private car service meets you inside the terminal with a name "
                            "board, tracks your flight and drives you straight to your hotel — no taxi queue, no "
                            "navigating an unfamiliar transit network."
                            % (ap.get("name_en") or (city + " Airport"), city,
                               (", roughly %d km from the city centre" % d) if d else "", ap.get("note_en") or "")))
    else:
        acards.append(acard("✈️ Airports", "No commercial airport in %s" % city,
                            "%s has no commercial passenger airport of its own, so most visitors arrive by rail or road "
                            "and transfer to a private car for the last leg. Your driver collects you at the station "
                            "or hotel and takes you straight to your destination in %s." % (city, city)))
    for extra in (f.get("airport_alt") or [])[:3]:
        acards.append(acard("✈️ %s" % extra.get("name_en", ""), "Secondary airport",
                            esc(extra.get("note_en") or "")))
    rcards = []
    if rw:
        st = rw.get("station_en") or (city + " Railway Station")
        rcards.append(acard("🚄 %s" % st, "Main rail station",
                            "%s is the principal rail station for %s%s. Taxis and buses meet arrivals at the station "
                            "forecourt; a pre-booked private car is the easiest way to reach hotels and sights beyond "
                            "the city centre." % (st, city,
                            ", with high-speed services on the national network" if rw.get("high_speed") else "")))
    else:
        rcards.append(acard("🚄 Rail connections", "Rail access to %s" % city,
                            "Rail travellers usually arrive through a neighbouring hub, then continue to %s by road. "
                            "Pre-booking a private car for that final leg avoids the transfer queues at bigger "
                            "stations." % city))
    rcards.append(acard("🛣️ By road", "Highways and expressways",
                        "%s is reached by expressway from the provincial capital and neighbouring prefecture cities. "
                        "Driving distances are usually 2–5 hours, and a private car is often the most comfortable way "
                        "to cover several sites in one day." % city))
    return """<!-- Getting to %s: Airports &amp; Railway Stations -->
 <section class="section" style="background:var(--color-gray-50);">
 <div class="container">
%s
 <h3 style="margin-bottom:var(--space-4);margin-top:var(--space-8);">✈️ Airports</h3>
 <div class="grid grid-2" style="gap: var(--space-6);">
%s
 </div>
 <h3 style="margin-bottom:var(--space-4);margin-top:var(--space-10);">🚄 Railway Stations</h3>
 <div class="grid grid-3" style="gap: var(--space-6);">
%s
 </div>
 </div>
 </section>
""" % (city, sec_header("Getting to %s: Airports &amp; Railway Stations" % city,
                         "How to reach %s by air, rail and road" % city),
       "\n".join(acards), "\n".join(rcards))

def build_food(city, f):
    if f.get("food_html"):
        food_body = f["food_html"]
    else:
        food_body = "".join("<p><strong>%s</strong> (%s) — %s</p>" %
                             (esc(i.get("name_en", "")), esc(i.get("name_cn", "")), esc(i.get("desc", "")))
                             for i in (f.get("food") or []))
    shop = f.get("shopping_html") or ("<p>Shopping in %s centres on the everyday commercial streets around the "
                                      "centre, where you will find local tea, snacks and crafts.</p>" % city)
    tea = f.get("tea_html") or ("<p>Tea culture runs through the day in %s: loose-leaf houses serve the region's own "
                                "greens in covered bowls, and the older teahouses are where the city's social life "
                                "happens.</p>" % city)
    return """<!-- Food &amp; Shopping -->
 <section class="section" style="background:var(--color-gray-50);">
 <div class="container">
%s
 <div class="grid grid-2" style="gap: var(--space-6);">
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🍽️ Must-Try %s Cuisine</h4>
 %s
 </div>
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🛍️ Shopping in %s</h4>
 %s
 </div>
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🍵 Tea &amp; Drinks</h4>
 %s
 </div>
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🚗 Private Car for a Food Crawl</h4>
 <p>A private car and driver lets you start at the morning market, cross the city for lunch, and finish at an
 evening teahouse without worrying about parking or the last bus back to your hotel.</p>
 </div>
 </div>
 </div>
 </section>
""" % (sec_header("Food &amp; Shopping in %s" % city, "What to eat and what to bring home from %s" % city),
       city, food_body, city, shop, tea)

def build_heritage(city, f):
    h = f.get("heritage_html") or ("<p>The old town core and its temple and guild-hall architecture carry most of "
                                   "%s's heritage, and the traditional crafts of the region are still practised "
                                   "there.</p>" % city)
    tea = f.get("tea_html") or ("<p>Tea culture runs through the day in %s: loose-leaf houses serve the region's own "
                                "greens in covered bowls.</p>" % city)
    return """<!-- Intangible Cultural Heritage &amp; Living Crafts -->
 <section class="section" style="background:var(--color-gray-50);">
 <div class="container">
%s
 <div class="grid grid-3" style="gap: var(--space-6);">
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🏛️ Heritage &amp; Landmarks</h4>
 %s
 </div>
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🏺 Local Crafts &amp; Products</h4>
 %s
 </div>
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🍵 Tea Culture</h4>
 %s
 </div>
 </div>
 </div>
 </section>
""" % (sec_header("Intangible Cultural Heritage &amp; Living Crafts in %s" % city,
                   "The living traditions of %s — the crafts, festivals and food that are still part of daily life." % city),
       h, h, tea)

def build_secrets(city, f, lm):
    secrets = f.get("local_secrets") or []
    if not secrets:
        secrets = ["Ask your driver to arrive early at the main sight, before the tour coaches.",
                   "Eat where the queues are shortest: the morning market and the small shops a block back from the square.",
                   "Distances inside %s look short on a map but stretch out in traffic — build in buffer time." % city]
    cards = []
    heads = ["🎭 Start at the landmark", "🥢 Skip the tourist menu", "⏱️ Plan the driving time", "📍 Ask the driver"]
    for i, s in enumerate(secrets):
        cards.append(""" <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">%s</h4>
 <p>%s</p>
 </div>""" % (heads[i % len(heads)], esc(s)))
    return """<!-- %s Local Secrets -->
 <section class="section">
 <div class="container">
%s
 <div class="grid grid-3" style="gap: var(--space-6);">
%s
 </div>
 </div>
 </section>
""" % (city, sec_header("%s Local Secrets" % city, "Insider tips to help you experience %s like a local" % city),
       "\n".join(cards))

def build_day_trips(city, f):
    trips = f.get("day_trips") or []
    cards = []
    for i, t in enumerate(trips):
        nm = t.get("name_en") or t.get("name_cn") or ""
        cn = t.get("name_cn") or ""
        cards.append(""" <div class="card" style="padding:var(--space-6);">
 <h3 class="lvl-h4">🚗 %s</h3>
 <p style="font-size:var(--text-sm);color:var(--color-gray-500);margin-bottom:var(--space-3);">%s</p>
 <p><strong>%s</strong> %s A private car takes you there and waits while you explore, then brings you back to %s
 in the evening.</p>
 </div>""" % (esc(nm), esc(t.get("duration") or "Half day"),
                esc(cn or nm), esc(t.get("desc") or ""), city))
    return """<!-- Day Trips from %s -->
 <section class="section">
 <div class="container">
%s
 <div class="grid grid-3">
%s
 </div>
 </div>
 </section>
""" % (city, sec_header("Day Trips from %s" % city,
                         "Three journeys worth the drive from %s — each one easy with a car and driver on standby." % city),
       "\n".join(cards))

def climate_season(months, idxs):
    """从逐月气候数据算出某季节的温区与降水"""
    if not months:
        return ""
    sel = [months[i - 1] for i in idxs if i - 1 < len(months) and months[i - 1]]
    if not sel:
        return ""
    tmax = [m["tmax"] for m in sel if m.get("tmax") is not None]
    tmin = [m["tmin"] for m in sel if m.get("tmin") is not None]
    prec = [m["prec"] for m in sel if m.get("prec") is not None]
    parts = []
    if tmax and tmin:
        parts.append("daytime %g–%g°C, nights around %g°C" % (min(tmax), max(tmax), min(tmin)))
    if prec:
        parts.append("about %d mm of precipitation a month" % int(round(sum(prec) / len(prec))))
    return "; ".join(parts)


def build_best_time(city, f, climate):
    bt = f.get("best_time") or {}
    summary = bt.get("summary") or ("The best window for %s depends on what you came for — mountains and grasslands "
                                    "are at their best in summer, while the towns and their markets run year-round."
                                    % city)
    months = (climate or {}).get("months") if climate else None
    seasons = [("Spring", bt.get("spring"), [3, 4, 5]), ("Summer", bt.get("summer"), [6, 7, 8]),
               ("Autumn", bt.get("autumn"), [9, 10, 11]), ("Winter", bt.get("winter"), [12, 1, 2])]
    cards = []
    for name, txt, idxs in seasons:
        ctext = climate_season(months, idxs)
        if txt and ctext:
            body = "%s (%s)" % (txt.rstrip("。"), ctext)
        elif txt:
            body = txt
        elif ctext:
            body = ctext
        else:
            continue
        em = {"Spring": "🌸", "Summer": "☀️", "Autumn": "🍂", "Winter": "❄️"}[name]
        cards.append(""" <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">%s %s</h4>
 <p>%s</p>
 </div>""" % (em, name, esc(body)))
    if not cards:
        cards = [""" <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🗓️ Year-round</h4>
 <p>%s</p>
 </div>""" % esc(summary)]
    return """<!-- Best Time to Visit %s -->
 <section class="section" style="background:var(--color-gray-50);">
 <div class="container">
%s
 <div class="grid grid-4" style="gap: var(--space-6);">
%s
 </div>
 </div>
 </section>
""" % (city, sec_header("Best Time to Visit %s" % city, summary), "\n".join(cards))

def build_phrases(city, f):
    items = [
        ("👋 Nǐ hǎo", "你好", "Hello / good day"),
        ("🙏 Xièxiè", "谢谢", "Thank you"),
        ("🚗 Wǒ xiǎng qù...", "我想去...", "I would like to go to..."),
        ("💰 Duōshao qián?", "多少钱？", "How much is it?"),
        ("🕐 Jǐ diǎn?", "几点？", "What time is it?"),
        ("📍 Zài nǎlǐ?", "在哪里？", "Where is it?"),
    ]
    cards = []
    for py, cn, en in items:
        cards.append(""" <div class="card" style="padding:var(--space-5);text-align:center;">
 <p style="font-size:var(--text-xl);font-weight:700;color:var(--color-primary);margin-bottom:var(--space-2);">%s</p>
 <p style="font-size:var(--text-sm);color:var(--color-gray-600);margin-bottom:var(--space-2);">%s</p>
 <p style="font-size:var(--text-sm);color:var(--color-gray-500);">%s</p>
 </div>""" % (esc(py), esc(cn), esc(en)))
    return """<!-- Useful Chinese Phrases for %s -->
 <section class="section">
 <div class="container">
%s
 <div class="grid grid-3" style="gap: var(--space-5);">
%s
 </div>
 </div>
 </section>
""" % (city, sec_header("Useful Chinese Phrases for %s" % city,
                         "Print these, or show your driver the Chinese on your phone — it makes every stop easier in %s." % city),
       "\n".join(cards))

def build_longtail(city, f, attrs):
    ap = f.get("airport")
    seat = f.get("seat_en") or city
    lm = attrs[0].get("name_en") if attrs else city
    legs = []
    if ap:
        legs.append(("%s Airport → %s" % (ap.get("name_en") or (city + " Airport"), city),
                     "Your driver meets the flight at the arrival hall, tracks delays and takes you straight to your hotel."))
    if f.get("railway"):
        st = f.get("railway").get("station_en") or (city + " Railway Station")
        legs.append(("%s → %s" % (st, city), "A single private car from the platform to your hotel or your first "
                     "sight — no waiting for a bus, no second taxi."))
    legs.append(("%s → %s" % (city, lm), "The classic day trip: the car waits at the entrance while you explore, "
                 "then takes you onward to the next stop."))
    legs.append(("%s → %s" % (city, city), "Full-day charter for families or small groups who want the car "
                 "and driver on call all day."))
    cards = []
    for title, desc in legs:
        cards.append(""" <div class="card" style="padding:var(--space-5);">
 <h4 style="margin-bottom:var(--space-2);">🚗 %s</h4>
 <p style="font-size:var(--text-sm);color:var(--color-gray-600);">%s</p>
 </div>""" % (esc(title), esc(desc)))
    return """<!-- Popular %s Airport Transfer Routes -->
 <section class="section" style="background:var(--color-gray-50);">
 <div class="container">
%s
 <div class="grid grid-2" style="gap: var(--space-6);">
%s
 </div>
 </div>
 </section>
""" % (city, sec_header("Popular %s Airport Transfer Routes" % city,
                         "The transfers we run most often around %s." % city), "\n".join(cards))

def build_cta(city, slug):
    return """<!-- Service CTA -->
 <section class="section" style="background:linear-gradient(135deg,var(--color-primary),var(--color-primary-dark));">
 <div class="container">
 <div style="text-align:center;max-width:760px;margin:0 auto;">
 <h2 id="toc-book-your-%s-airport-transfer" style="color:var(--color-white);margin-bottom:var(--space-4);">Book Your %s Airport Transfer</h2>
 <p style="color:rgba(255,255,255,0.9);font-size:var(--text-lg);margin-bottom:var(--space-6);">Tell us your flight
 number and we will handle the rest — a named driver, a tracked flight and a fixed price agreed before you travel.</p>
 <div style="display:flex;gap:var(--space-4);justify-content:center;flex-wrap:wrap;">
 <a href="/booking.html?city=%s" class="btn btn-lg" style="background:var(--color-white);color:var(--color-primary);">Book Now</a>
 <a href="/contact.html" class="btn btn-lg btn-outline" style="color:var(--color-white);border-color:var(--color-white);">Ask a Question</a>
 </div>
 </div>
 </div>
 </section>
""" % (slug, city, slug)

def build_essentials(city, f):
    return """<!-- Travel Essentials -->
 <section class="section">
 <div class="container">
%s
 <div class="grid grid-3" style="gap: var(--space-6);">
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🗣️ English-Speaking Guide</h4>
 <p style="margin-bottom:var(--space-3);">Every Chinawheely driver speaks English and knows %s's main sights, so you
 get local commentary on the way, not just a ride.</p>
 <p>Ask for a guide-driver if you want a full day with someone who can explain the history behind what you see.</p>
 </div>
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🎫 Tickets &amp; Permits</h4>
 <p style="margin-bottom:var(--space-3);">National parks, temples and museums in %s usually sell tickets on site;
 popular sites can sell out early in the season.</p>
 <p>Border and restricted-area destinations need permits arranged in advance — tell us the exact places on your
 itinerary and we will flag anything that needs paperwork.</p>
 </div>
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🏥 Medical Services</h4>
 <p style="margin-bottom:var(--space-3);">Add a health checkup, dental service or hospital visit to your transfer
 booking.</p>
 <p>Our partner hospitals in %s cover general practice, emergency care and routine dental work for travellers, and
 the driver will wait with you.</p>
 </div>
 </div>
 </div>
 </section>
""" % (sec_header("Travel Essentials for Your %s Trip" % city,
                   "Practical details that make the difference between a smooth trip and a stressful one in %s." % city), city, city, city)

def build_tea(city, f):
    tea = f.get("tea_html") or ("<p>Tea culture runs through the day in %s: loose-leaf houses serve the region's own "
                                "greens in covered bowls, and the older teahouses are where the city's social life "
                                "happens.</p>" % city)
    heritage = f.get("heritage_html") or ""
    return """<!-- Tea Culture &amp; Teahouse Guide -->
 <section class="section" style="background:var(--color-gray-50);">
 <div class="container">
%s
 <div class="grid grid-3" style="gap: var(--space-6);">
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🍵 Tea Houses of %s</h4>
 %s
 </div>
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">🫖 A Gongfu Tasting</h4>
 <p>Ask your driver to stop at a house where the tea is brewed properly: a small pot, several cups, and a host who
 will explain how the leaves change as the water cools. It is the cheapest and most relaxing hour of the day.</p>
 </div>
 <div class="card" style="padding:var(--space-6);">
 <h4 style="margin-bottom:var(--space-3);">💡 Tea Etiquette Tips</h4>
 <p style="margin-bottom:var(--space-3);">Pour for others before yourself, and pour with the other hand as a small
 sign of respect. Tapping two fingers on the table is the traditional way to say thank you.</p>
 <p>Most houses will refill your covered bowl for free — there is no need to order again.</p>
 </div>
 </div>
 </div>
 </section>
""" % (sec_header("Tea Culture &amp; Teahouse Guide in %s" % city,
                   "What to drink in %s, where to drink it, and how the locals do it." % city), city, tea)

# ---------------- 组装 ----------------
def build_page(slug, f, pe, climate, img, photo, province_cities):
    global TPLOBJ
    if TPLOBJ is None:
        TPLOBJ = Tpl()
    city = f.get("city_en") or slug
    city_cn = f.get("city_cn") or ""
    prov = f.get("province_en") or ""
    prov_cn = f.get("province_cn") or ""
    ap = f.get("airport")
    attrs = f.get("attractions") or []
    desc = ("Private car and airport transfer service in %s%s. Fixed price, licensed English-speaking drivers, "
            "flight tracking and door-to-door hotel transfers across %s."
            % (city, (" (%s)" % prov) if prov else "", city))
    title = ("%s Airport Transfer & Private Car | ChinaWheely" % city) if ap else \
            ("%s Private Car & Transfer Service | ChinaWheely" % city)
    keywords = ("%s airport transfer, %s car rental with driver, %s private car, %s taxi, %s transfer, %s tourism"
                % (city, city, city, city, city, city))

    # 价格标签（用于 Popular Routes 卡片）
    ap_data = (pe.get("airport") or {})
    p = []
    for key in ["sedan_economy", "sedan_comfort", "suv_7", "minivan_9"]:
        v = ap_data.get(key)
        p.append(money(v.get("pkg")) if v else "On request")
    while len(p) < 4:
        p.append(p[-1])

    main = []
    main.append(build_hero(city, slug, ap, img, photo))
    gal = build_gallery(city, slug)
    if gal:
        main.append(gal)
    if f.get("photo_spots"):
        main.append(build_photo_spots(city, f["photo_spots"]))
    main.append(build_overview(city, f))
    if attrs:
        main.append(build_attractions(city, attrs))
    main.append(build_routes(city, f, attrs, p, ap))
    main.append(build_price(city, city_cn, pe, bool(ap)))
    main.append(build_getting(city, f))
    main.append(build_food(city, f))
    main.append(build_heritage(city, f))
    main.append(build_secrets(city, f, attrs[0].get("name_en") if attrs else None))
    main.append(build_day_trips(city, f))
    main.append(build_best_time(city, f, climate))
    main.append(build_phrases(city, f))
    main.append(build_longtail(city, f, attrs))
    main.append(build_cta(city, slug))
    main.append(build_essentials(city, f))
    main.append(build_tea(city, f))

    ld_blocks = [
        ld_json({"@context": "https://schema.org", "@type": "TravelAgency", "name": "Chinawheely %s" % city,
                 "url": SITE + "/", "logo": SITE + "/images/logo.webp", "description": desc,
                 "address": {"@type": "PostalAddress", "addressLocality": "Beijing", "addressCountry": "CN"},
                 "areaServed": {"@type": "City", "name": city}, "priceRange": "¥¥"}),
        ld_json({"@context": "https://schema.org", "@type": "BreadcrumbList",
                 "itemListElement": [
                     {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                     {"@type": "ListItem", "position": 2, "name": "Cities", "item": SITE + "/cities.html"},
                     {"@type": "ListItem", "position": 3, "name": city, "item": "%s/%s.html" % (SITE, slug)}]}),
    ]
    # City JSON-LD（放 body）
    city_schema = {"@context": "https://schema.org", "@type": "City", "name": city,
                   "alternateName": city_cn, "description": desc, "url": "%s/%s.html" % (SITE, slug),
                   "image": "%s/%s" % (SITE, img.lstrip("/")),
                   "containedInPlace": {"@type": "Province", "name": prov}}
    if f.get("area_km2"):
        city_schema["area"] = {"@type": "QuantitativeValue", "value": f["area_km2"], "unitCode": "KMK"}
    if f.get("population"):
        city_schema["population"] = {"@type": "QuantitativeValue", "value": f["population"]}
    ld_blocks.append(ld_json(city_schema))

    head = build_head(city, slug, img, title, desc, keywords, ld_blocks[:2])
    nav = TPLOBJ.nav.replace("Xiangyang", city).replace("xiangyang", slug).replace("襄阳", city_cn)
    body_main = "<main>\n" + "\n".join(main)
    city_ld_block = ld_blocks[2]

    tail = TPLOBJ.tail
    # footer 里的城市/省份 token
    tail = re.sub(r'<script type="application/ld\+json">\s*\{[^{}]*"@type": "City".*?</script>\n?', "", tail, flags=re.S)
    tail = tail.replace("Xiangyang", city).replace("襄阳", city_cn)
    tail = tail.replace("Hubei", prov).replace("湖北", prov_cn)
    tail = tail.replace("xiangyang", slug)
    tail = tail.replace("Xiangyang Liuji Airport", ap.get("name_en") if ap else "%s Transfer" % city)
    tail = tail.replace("Liuji Airport", ap.get("name_en") if ap else "%s Transfer" % city)
    # footer 里的「Other cities in Hubei」内链清单
    hub = "".join('<li><a href="%s.html">%s</a></li>' % (s, n) for s, n in province_cities)
    tail = re.sub(r'<ul class="cwf-links">.*?</ul>', '<ul class="cwf-links">%s</ul>' % hub, tail, count=1, flags=re.S)
    tail = re.sub(r"<h3>Other cities in [^<]+</h3>", "<h3>Other cities in %s</h3>" % prov, tail, count=1)

    page = head + nav + body_main + "\n" + city_ld_block + "\n" + tail
    return page


def main():
    global TPLOBJ
    TPLOBJ = Tpl()
    only = sys.argv[1] if len(sys.argv) > 1 else None
    force = "--force" in sys.argv
    pricing = json.load(open(os.path.join(REPO, "pricing", "pricing.json"), encoding="utf-8"))["cities"]
    global CITY_INDEX
    CITY_INDEX = load_city_index()
    files = sorted(glob.glob(os.path.join(FACTS, "*.json")))
    made, skipped, missing = [], [], []
    for p in files:
        b = os.path.basename(p)
        if b.startswith("climate_") or b == "SCHEMA.md":
            continue
        try:
            f = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print("!! 读取失败", b, e)
            continue
        slug = f.get("slug") or b[:-5]
        if only and slug != only:
            continue
        out = os.path.join(REPO, slug + ".html")
        if os.path.exists(out) and not force:
            skipped.append(slug)
            continue
        pe = pricing.get(slug)
        if not pe:
            missing.append(slug)
            continue
        clim_path = os.path.join(FACTS, "climate_%s.json" % slug)
        climate = json.load(open(clim_path, encoding="utf-8")) if os.path.exists(clim_path) else None
        photo = os.path.exists(os.path.join(REPO, "images", slug + ".webp"))
        img = ("images/%s.webp" % slug) if photo else "images/placeholder-city.webp"
        prov = f.get("province_en") or ""
        prov_sec = (f.get("province_section") or prov.lower().replace(" ", "-"))
        province_cities = [(s, n) for s, n in CITY_INDEX.get(prov_sec, []) if s != slug]
        page = build_page(slug, f, pe, climate, img, photo, province_cities)
        write(out, page)
        made.append(slug)
        print("生成 %s.html  (%d KB)" % (slug, len(page.encode("utf-8")) // 1024))
    print("\n生成 %d / 跳过(已存在) %d / 缺价格条目 %d" % (len(made), len(skipped), len(missing)))
    if missing:
        print("缺 pricing.json 条目:", ", ".join(missing))


def load_city_index():
    """从 cities.html 解析 {省份id: [(slug, 英文名), ...]}"""
    h = read(os.path.join(REPO, "cities.html"))
    idx = {}
    for m in re.finditer(r'<section class="prov-sec" id="prov-([^"]+)">(.*?)</section>', h, re.S):
        sec, body = m.group(1), m.group(2)
        for mm in re.finditer(r'<li><a href="([a-z0-9_]+)\.html"><span class="cname">([^<]*)</span><span class="cen">([^<]*)</span></a></li>', body):
            idx.setdefault(sec, []).append((mm.group(1), mm.group(3)))
    return idx


CITY_INDEX = {}

if __name__ == "__main__":
    import glob
    main()

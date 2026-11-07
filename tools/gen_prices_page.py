#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P3 —— 生成 prices.html 静态价格总览页（全量可抓取）+ 更新 sitemap
用法: python3 tools/gen_prices_page.py [--dry]
"""
import html
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = "--dry" in sys.argv

data = json.load(open(os.path.join(BASE, "pricing", "pricing.json"), encoding="utf-8"))
CITIES = data["cities"]
META = data["meta"]
RATE = META["usdCnyRate"]


def usd(c):
    return round(c / RATE, 2)


def U(c):
    return f'≈ ${usd(c)}'


parts = []
n_cities = len(CITIES)
ORDERED = sorted(CITIES.items(), key=lambda kv: (0, kv[1]["en"]) if kv[0] == "beijing" else (1, kv[1]["en"]))
itemlist = json.dumps([
    {"@type": "ListItem", "position": i, "name": c["en"],
     "url": f"https://www.chinawheely.com/{slug}.html"}
    for i, (slug, c) in enumerate(ORDERED, 1)
], ensure_ascii=False)
parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Published Transfer &amp; Charter Prices 2026 — {n_cities} Cities | Chinawheely</title>
<meta name="description" content="Full published price list for Chinawheely airport transfers, intercity transfers and hourly charters in {n_cities} Chinese cities. Fixed prices in CNY with USD reference. No hidden fees.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://www.chinawheely.com/prices.html">
<link rel="icon" type="image/x-icon" href="favicon.ico">
<meta property="og:type" content="website">
<meta property="og:title" content="Published Transfer &amp; Charter Prices — {n_cities} Chinese Cities | Chinawheely">
<meta property="og:description" content="Fixed, published prices for airport transfers and hourly charters in {n_cities} Chinese cities. CNY with USD reference.">
<meta property="og:url" content="https://www.chinawheely.com/prices.html">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="https://www.chinawheely.com/images/beijing.webp">
<meta property="og:image:width" content="800">
<meta property="og:image:height" content="533">
<meta name="twitter:site" content="@chinawheely"/>
<meta name="twitter:card" content="summary_large_image">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://fonts.googleapis.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https: https://www.google-analytics.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self' https://www.google-analytics.com https://region1.google-analytics.com https://api.chinawheely.com https://open.er-api.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self';">
<script type="application/ld+json">
{{
 "@context": "https://schema.org",
 "@type": "WebPage",
 "@id": "https://www.chinawheely.com/prices.html#webpage",
 "url": "https://www.chinawheely.com/prices.html",
 "name": "Published Transfer & Charter Prices — {n_cities} Chinese Cities",
 "description": "Full published price list for Chinawheely airport transfers, intercity transfers and hourly charters in {n_cities} Chinese cities. Fixed prices in CNY with USD reference.",
 "inLanguage": "en",
 "isPartOf": {{
  "@type": "WebSite",
  "name": "Chinawheely",
  "url": "https://www.chinawheely.com"
 }}
}}
</script>
<script type="application/ld+json">
{{
 "@context": "https://schema.org",
 "@type": "ItemList",
 "name": "Chinawheely published transfer prices by city",
 "numberOfItems": {n_cities},
 "itemListElement": {itemlist}
}}
</script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color:#1f2937;line-height:1.6;background:#f8fafc}}
.container{{max-width:1180px;margin:0 auto;padding:0 20px}}
header{{background:#1B4D3E;color:#fff;padding:44px 0 36px}}
header h1{{font-size:30px;margin-bottom:8px}}
header p{{opacity:.9;max-width:780px}}
.rate-badge{{display:inline-block;margin-top:14px;padding:6px 14px;border:1px solid rgba(255,255,255,.4);border-radius:999px;font-size:13px}}
main{{padding:32px 0 60px}}
.intro{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:22px 26px;margin-bottom:28px}}
.intro h2{{font-size:20px;margin-bottom:10px}}
.intro ul{{margin:10px 0 0 20px}}
.intro li{{margin:5px 0;color:#475569}}
.toolbar{{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:22px}}
.toolbar input,.toolbar select{{padding:10px 14px;border:1px solid #cbd5e1;border-radius:10px;font-size:14px;background:#fff}}
.toolbar input{{flex:1;min-width:220px}}
.city{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;margin-bottom:16px;overflow:hidden}}
.city>summary{{cursor:pointer;padding:16px 22px;display:flex;justify-content:space-between;align-items:center;gap:14px;list-style:none}}
.city>summary::-webkit-details-marker{{display:none}}
.city>summary:hover{{background:#f1f5f9}}
.city-name{{font-weight:700;font-size:17px}}
.city-from{{font-size:13px;color:#64748b}}
.city-from strong{{color:#dc2626;font-size:15px}}
.city-body{{padding:4px 22px 22px;border-top:1px solid #e2e8f0}}
h3.tbl-title{{font-size:15px;margin:20px 0 8px;color:#0f172a}}
table{{width:100%;border-collapse:collapse;font-size:14px;margin-bottom:6px}}
th,td{{padding:9px 10px;text-align:left;border-bottom:1px solid #eef2f6}}
th{{background:#f8fafc;font-weight:600;color:#475569;font-size:13px}}
td.price{{font-weight:700;color:#dc2626;white-space:nowrap}}
td.usd{{color:#64748b;white-space:nowrap}}
.notes{{font-size:13px;color:#64748b;margin-top:8px}}
.book-cta{{display:inline-block;margin-top:12px;padding:9px 18px;background:#1B4D3E;color:#fff;border-radius:10px;text-decoration:none;font-size:14px}}
.city-guide-link{{display:inline-block;margin-top:12px;margin-right:10px;color:#1B4D3E;font-weight:600;font-size:14px;text-decoration:underline}}
.book-cta:hover{{background:#16382d}}
footer{{background:#0f2b23;color:#cbd5e1;padding:28px 0;font-size:14px}}
footer a{{color:#fff}}
@media(max-width:640px){{.city>summary{{flex-direction:column;align-items:flex-start}}table{{font-size:12px}}th,td{{padding:6px 6px}}}}
</style>
</head>
<body>
<header>
 <div class="container">
 <h1>Published Transfer &amp; Charter Prices</h1>
 <p>Every price below is a fixed, published rate for inbound travellers — airport transfers, intercity transfers and hourly charters across {len(CITIES)} Chinese cities. The price you see is the price you pay.</p>
 <span class="rate-badge">All prices in CNY &middot; USD reference at 1 USD = {RATE} CNY &middot; Updated {META.get('generatedAt', '2026')}</span>
 </div>
</header>
<main>
 <div class="container">
 <div class="intro">
 <h2>How our pricing works</h2>
 <ul>
 <li><strong>Airport transfers</strong> — a fixed package price covering up to 35&nbsp;km. Overtime is charged per minute and extra distance per kilometre, both published below.</li>
 <li><strong>Intercity transfers</strong> — priced at the same published rate as airport transfers from the departure city.</li>
 <li><strong>Hourly charters</strong> — a package price bundling the stated hours and distance, from 2&nbsp;h&nbsp;/&nbsp;35&nbsp;km up to 10&nbsp;h&nbsp;/&nbsp;125&nbsp;km.</li>
 <li><strong>Overtime and overage</strong> — charged transparently at the per-minute and per-kilometre rate shown for each city and vehicle.</li>
 <li><strong>Other cities</strong> — anywhere without a published table is quoted on request, usually within 2 hours.</li>
 </ul>
 </div>
 <div class="toolbar">
 <input type="search" id="q" placeholder="Search city (English or Chinese)…" aria-label="Search city">
 <select id="prod" aria-label="Filter by product">
 <option value="all">All products</option>
 <option value="airport">Airport &amp; intercity only</option>
 <option value="charter">Hourly charters only</option>
 </select>
 </div>
""")

ordered = ORDERED

for slug, c in ordered:
    a_vals = [v for v in c.get("airport", {}).values() if v.get("pkg") is not None]
    ch_vals = c.get("charter", {})
    floors = [v["pkg"] for v in a_vals] + \
             [t["pkg"] for veh in ch_vals.values() for t in veh.get("tiers", {}).values()]
    from_cny = min(floors) if floors else None
    from_txt = (f'<strong>From ¥{from_cny}</strong> (≈ ${usd(from_cny)})' if from_cny
                else 'Quote on request')
    parts.append(f'<details class="city" data-slug="{slug}" data-cn="{html.escape(c["cn"])}" '
                 f'data-en="{html.escape(c["en"])}"{" open" if slug == "beijing" else ""}>')
    parts.append(f'<summary><span class="city-name">{html.escape(c["cn"])} {html.escape(c["en"])}</span>'
                 f'<span class="city-from">{from_txt}</span></summary>')
    parts.append('<div class="city-body">')

    if a_vals:
        parts.append('<h3 class="tbl-title">Airport &amp; Intercity Transfer (package includes 35 km)</h3>')
        parts.append('<table><thead><tr><th>Vehicle</th><th>Seats</th><th>Luggage</th>'
                     '<th>Package</th><th>USD</th><th>Overtime /min</th><th>Extra /km</th></tr></thead><tbody>')
        for vkey, v in c.get("airport", {}).items():
            if v.get("pkg") is None:
                continue
            pm = f'¥{v["perMin"]}' if v.get("perMin") is not None else '—'
            pk = f'¥{v["perKm"]}' if v.get("perKm") is not None else '—'
            parts.append(f'<tr><td>{html.escape(v["name"])}</td><td>{v["seats"]}</td><td>{v["bags"]}</td>'
                         f'<td class="price">¥{v["pkg"]}</td><td class="usd">{U(v["pkg"])}</td>'
                         f'<td>{pm}</td><td>{pk}</td></tr>')
        parts.append('</tbody></table>')

    if ch_vals:
        parts.append('<h3 class="tbl-title">Hourly Charter (hours / distance included)</h3>')
        parts.append('<table><thead><tr><th>Vehicle</th><th>Package</th><th>Hours</th><th>KM incl.</th>'
                     '<th>Price</th><th>USD</th><th>Overtime /min</th><th>Extra /km</th></tr></thead><tbody>')
        for vkey, v in ch_vals.items():
            for tk, t in v.get("tiers", {}).items():
                pm = f'¥{t["perMin"]}' if t.get("perMin") is not None else '—'
                pk = f'¥{t["perKm"]}' if t.get("perKm") is not None else '—'
                parts.append(f'<tr><td>{html.escape(v["name"])}</td><td>{html.escape(t["name"])}</td>'
                             f'<td>{t["hours"]}</td><td>{t["includedKm"]}</td>'
                             f'<td class="price">¥{t["pkg"]}</td><td class="usd">{U(t["pkg"])}</td>'
                             f'<td>{pm}</td><td>{pk}</td></tr>')
        parts.append('</tbody></table>')

    parts.append('<p class="notes">Prices include vehicle, driver, fuel, tolls and standard insurance. '
                 'Overtime beyond the included time and distance is charged at the published rates above. '
                 'Final price is confirmed by our team before dispatch.</p>')
    parts.append(f'<a class="city-guide-link" href="{slug}.html">{html.escape(c["en"])} city guide &rarr;</a> ')
    parts.append(f'<a class="book-cta" href="booking.html">Book {html.escape(c["en"])} transfer</a>')
    parts.append('</div></details>')

parts.append(""" </div>
</main>
<footer>
 <div class="container">
 <p>Chinawheely — inbound private car, airport and intercity transfer services across China. Licensed travel agency L-HUB-101603.</p>
 <p><a href="booking.html">Book now</a> &middot; <a href="contact.html">Request a quote</a> &middot; <a href="index.html">Home</a></p>
 </div>
</footer>
<script>
(function () {
  var q = document.getElementById('q');
  var prod = document.getElementById('prod');
  var cities = Array.prototype.slice.call(document.querySelectorAll('.city'));
  function apply() {
    var term = (q.value || '').trim().toLowerCase();
    cities.forEach(function (c) {
      var cn = c.getAttribute('data-cn').toLowerCase();
      var en = c.getAttribute('data-en').toLowerCase();
      var match = !term || cn.indexOf(term) >= 0 || en.indexOf(term) >= 0;
      if (!match) { c.style.display = 'none'; return; }
      var titles = Array.prototype.slice.call(c.querySelectorAll('h3.tbl-title'))
        .map(function (t) { return t.textContent; });
      if (prod.value === 'airport') {
        c.style.display = titles.some(function (t) { return /Airport/.test(t); }) ? '' : 'none';
      } else if (prod.value === 'charter') {
        c.style.display = titles.some(function (t) { return /Charter/.test(t); }) ? '' : 'none';
      } else {
        c.style.display = '';
      }
    });
  }
  q.addEventListener('input', apply);
  prod.addEventListener('change', apply);
  apply();
})();
</script>
</body>
</html>
""")

prices_html = "\n".join(parts)
if not DRY:
    open(os.path.join(BASE, "prices.html"), "w", encoding="utf-8").write(prices_html)
print(f"prices.html: {len(prices_html)/1024:.1f} KB, {len(ordered)} 城市")

# ---------------------------------------------------------------- sitemap
sm_path = os.path.join(BASE, "sitemap.xml")
sm = open(sm_path, encoding="utf-8").read()
if "prices.html" in sm:
    print("sitemap.xml: prices.html 已存在")
else:
    m = re.search(r"(  <url>\s*<loc>[^<]*?/about\.html</loc>.*?</url>)\s*", sm, re.S)
    if m:
        entry = m.group(1)
        new_entry = entry.replace("/about.html", "/prices.html")
        sm = sm.replace(entry, entry + "\n" + new_entry, 1)
        if not DRY:
            open(sm_path, "w", encoding="utf-8").write(sm)
        print("sitemap.xml: 已加入 prices.html")
    else:
        print("⚠ sitemap.xml 未找到 about.html 模板")

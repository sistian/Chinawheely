#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P5e —— 让报价区块按城市个性化（避免 280 页文案雷同被搜索引擎降权）

个性化来源：/Users/w/.openclaw/workspace/city_facts/*.json 里的真实数据
  · 城市英文名 / 中文名 / 省份
  · 机场名称、铁路站、交通类型
  · 面积 / 人口
个性化内容：
  · 标题里带省份，例："What Your Danzhou (Hainan) Ride Will Cost"
  · 第一条说明里带上真实机场名 / 火车站
  · 一句本地化提示，用真实交通类型
  · 区块内的优势卡片文案按城市轮换（多套模板，确定性选择，保证同页稳定）

用法: python3 tools/personalize_quote_blocks.py
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = "/Users/w/.openclaw/workspace/city_facts"

MARK = "<!-- CW:QUOTE-BLOCK -->"
END = "<!-- /CW:QUOTE-BLOCK -->"

SKIP_SLUGS = {
    "index", "prices", "booking", "contact", "about", "services", "help",
    "terms", "privacy", "careers", "partners", "cookies", "cancellation",
    "404", "manage-order", "thank-you", "admin", "admin-login",
    "seo-swot-analysis", "image_downloader", "batch_download", "get-quote", "faq",
}
THEME_PAT = re.compile(
    r"(tea-culture|best-time|day-trips|photo-spots|food-shopping|"
    r"airport-transfer-to|detailed|guide)", re.I)

# 4 套「优势」文案，按城市名稳定轮换 —— 同样的事实，不同的表达
ADV_SETS = [
    [
        ("🛡️", "A licensed travel agency, not a broker",
         "Chinawheely is a registered travel agency (L-HUB-101603). Your booking is a contract "
         "with a licensed operator, and the driver you are given is ours to account for."),
        ("🔒", "One price, in writing, before you travel",
         "Tolls, parking, driver service and free airport waiting are inside the fare. "
         "No surge pricing, no meter, nothing collected on the road."),
        ("✈️", "We watch your flight, the wait is ours",
         "Send your flight number and we track it live. If the delay is ours to absorb, "
         "it never reaches your bill."),
        ("🧑‍✈️", "A local driver who knows the shortcuts",
         "Your driver lives here and drives here, so the route, the parking and the "
         "shortcuts are already known."),
        ("⏱️", "Free changes until 48 hours out",
         "Plans move. Reschedule or cancel free of charge up to 48 hours before pickup, "
         "straight from your confirmation."),
        ("💬", "A person answers, 08:00–24:00 Beijing time",
         "One WhatsApp message reaches someone who can re-price, re-route or re-plan your "
         "day on the spot."),
    ],
    [
        ("🛡️", "Licensed, insured and accountable",
         "We are a registered travel agency (L-HUB-101603), not an app that passes your "
         "number to whoever is free. The licence is ours to put behind the promise."),
        ("🔒", "Fixed fare, all-inclusive",
         "Driver, fuel, tolls, parking and airport waiting sit inside one number that you "
         "confirm before booking. No meter, no surge, no surprise at the kerb."),
        ("✈️", "Your flight, our watch",
         "We track the flight in real time and hold the driver accordingly. Late landing "
         "on our side of the line is absorbed by us."),
        ("🧑‍✈️", "Driven by someone who knows the region",
         "Our drivers are local. They arrive early, they know which gate the terminal exit "
         "is, and they know where to actually park near the places you are going."),
        ("⏱️", "Change it, cancel it, no argument",
         "Anything up to 48 hours before pickup can be changed or cancelled free, from the "
         "link in your confirmation email."),
        ("💬", "Real support, real hours",
         "WhatsApp reaches a human between 08:00 and 24:00 Beijing time — someone who can "
         "change the quote, not just read it."),
    ],
    [
        ("🛡️", "We are the operator, not the middleman",
         "Registered travel agency L-HUB-101603. The car, the driver and the contract are "
         "ours, which is why we can put a fixed number on them."),
        ("🔒", "One price covers the whole ride",
         "Everything that normally gets added later — tolls, parking, driver service, the "
         "wait at the terminal — is already inside the fare you see."),
        ("✈️", "Delays are handled, not billed",
         "We monitor your flight live and adjust the pickup automatically. Waiting time "
         "because of a delay does not become your cost."),
        ("🧑‍✈️", "A driver who belongs to the city",
         "Local knowledge is not a selling point we borrow — it is who we hire. The route "
         "between the airport and your hotel is somebody's daily drive."),
        ("⏱️", "48 hours of free flexibility",
         "Change or cancel free right up to 48 hours before your pickup time. No admin "
         "charge, no argument."),
        ("💬", "Answered by a person who can act",
         "08:00–24:00 Beijing time on WhatsApp. Ask for a different car, a different route "
         "or a different price — you get an answer."),
    ],
    [
        ("🛡️", "A real licence behind the booking",
         "L-HUB-101603, a registered travel agency. When something goes wrong, there is a "
         "company answerable for it — not just a driver at the kerb."),
        ("🔒", "The quote is the invoice",
         "The fare covers driver, fuel, tolls, parking and airport waiting time. Nothing "
         "appears on the day that was not on the quote."),
        ("✈️", "Flight tracking, automatic pickup adjustment",
         "Give us the flight number and we follow it. The driver shifts with the delay, "
         "and the clock does not start against you."),
        ("🧑‍✈️", "Local drivers, local knowledge",
         "Your driver knows the airport layout, the traffic patterns and the parking near "
         "your destination. That is not something a call centre can fake."),
        ("⏱️", "Free cancellation up to 48 hours before",
         "The booking link in your confirmation lets you reschedule or cancel at no cost "
         "until 48 hours before pickup."),
        ("💬", "Support that can still say yes",
         "WhatsApp, 08:00–24:00 Beijing time. Ask for an upgrade, an extra hour or a "
         "different city and we will price it on the spot."),
    ],
]


def esc(s):
    import html
    s = html.escape(str(s), quote=False)
    for ent in ("mdash", "yen", "nbsp", "amp", "rarr", "lt", "gt", "quot", "apos", "ndash"):
        s = s.replace("&amp;" + ent + ";", "&" + ent + ";")
    return s


def load_facts(slug, city_en=None):
    p = os.path.join(FACTS, slug + ".json")
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            pass
    # 回退：只用省份映射表，至少能把省份填上
    try:
        sys.path.insert(0, os.path.join(BASE, "tools"))
        import city_province_map as M
        # 映射表以英文城市名为 key（含 'Karakax (Hotan)' 这类复合名）
        cands = []
        if city_en:
            cands += [city_en, city_en.title(), city_en.split("(")[0].strip()]
        cands += [slug.replace("_", " ").title(), slug.replace("_", " ")]
        # 复合名：Karakax Hotan → 映射表里的 'Karakax (Hotan)'
        if city_en and " " in city_en:
            a, b = city_en.split(" ", 1)
            cands += [f"{a} ({b})", f"{a} {b}"]
        # slug 形式：Yichun_hlj → 'Yichun Hlj'，映射表里是 'Yichun_Heilongjiang'
        for sep in ("_", " "):
            parts = slug.split(sep)
            if len(parts) == 2:
                cands += [parts[0] + sep + parts[1].capitalize(),
                          parts[0] + sep + parts[1].title()]
                # yichun_hlj → Yichun_Hlj / Yichun_Heilongjiang（缩写补全）
                abbr = {"hlj": "Heilongjiang", "jx": "Jiangxi", "js": "Jiangsu",
                        "zj": "Zhejiang", "ah": "Anhui", "gd": "Guangdong",
                        "hb": "Hubei", "hn": "Hunan", "sc": "Sichuan",
                        "sd": "Shandong", "gx": "Guangxi", "nm": "Inner Mongolia",
                        "xj": "Xinjiang", "xz": "Tibet", "yn": "Yunnan",
                        "gs": "Gansu", "nx": "Ningxia", "qh": "Qinghai",
                        "zj2": "Zhejiang", "fj": "Fujian", "jx2": "Jiangxi",
                        "ha": "Henan", "hb2": "Hubei", "hl": "Heilongjiang",
                        "sn": "Shaanxi", "zj3": "Zhejiang", "cq": "Chongqing",
                        "bj": "Beijing", "sh": "Shanghai", "tj": "Tianjin"}
                full = abbr.get(parts[1].lower())
                if full:
                    cands += [parts[0].capitalize() + sep + full,
                              parts[0].title() + sep + full]
        for cand in cands:
            prov = M.CITY_PROV.get(cand)
            if prov:
                return {"province_en": prov}
        # 忽略大小写再试
        low = {k.lower(): v for k, v in M.CITY_PROV.items()}
        for cand in cands:
            prov = low.get(cand.lower())
            if prov:
                return {"province_en": prov}
    except Exception:
        pass
    return None


def pick_adv(city_en):
    idx = sum(ord(ch) for ch in city_en) % len(ADV_SETS)
    return ADV_SETS[idx]


def build_personalized(slug, city_en, samples):
    fa = load_facts(slug, city_en) or {}
    prov = fa.get("province_en")
    # h1 本身带省份时直接用（如 "Yichun, Heilongjiang"）
    if not prov and "," in city_en:
        cand = city_en.split(",", 1)[1].strip()
        if cand and len(cand) < 30:
            prov = cand
    cn = fa.get("city_cn")
    ap = fa.get("airport") or {}
    ap_name = ap.get("name_en")
    rail = fa.get("railway") or {}
    rail_name = rail.get("name_en") if isinstance(rail, dict) else None
    ttype = fa.get("transport_type")

    # 标题带省份
    title_city = f"{city_en} ({prov})" if prov else city_en

    # 本地化交通提示
    bits = []
    if ap_name:
        bits.append(f"your airport pickup at {ap_name}")
    if rail_name and rail_name != ap_name:
        bits.append(f"your {rail_name} collection")
    if ttype:
        bits.append(f"{ttype.lower()} transfers")
    local_line = "; ".join(bits) if bits else "your arrival transfer"

    # 个性化说明句
    if prov:
        lead = (f"{city_en} is in {prov}, and it is not on our published price list yet — "
                f"so we quote it for you. Here is exactly how the number is built for {local_line}, "
                f"and what you get for it.")
    else:
        lead = (f"{city_en} is not on our published price list yet — so we quote it for you. "
                f"Here is exactly how the number is built for {local_line}, and what you get for it.")

    # 「价格怎么算」的 4 条说明：按城市的真实交通类型挑选，让文案随城市变化
    B = {
        "airport": [
            "Your vehicle sets the base. 4-seat economy sedan for a couple of bags, 4-seat "
            "comfort sedan for a longer road, 6-seat MPV for a family, 8-11 seat van for a group, "
            "up to a 55-seat coach for a delegation.",
            f"Distance and time are measured, not guessed. From {ap_name or 'the airport'} into "
            f"the city, or a one-way city-to-city run, the fare moves with the kilometres and the "
            f"hours you actually use.",
            "Everything is inside the fare. Tolls, parking, driver service and free airport "
            "waiting time are all included. There is no surge multiplier, no meter, and no "
            "cash-on-the-day surprise.",
            "Intercity is the same price as the airport run. City-to-city transfers do not carry "
            "an airport surcharge - the rate you see for the airport is the rate you get between "
            "cities.",
        ],
        "rail": [
            "Your vehicle sets the base. 4-seat economy sedan for a couple of bags, 4-seat "
            "comfort sedan for a longer road, 6-seat MPV for a family, 8-11 seat van for a group, "
            "up to a 55-seat coach for a delegation.",
            f"Distance and time are measured, not guessed. From {rail_name or ap_name or 'the station'} "
            f"to your hotel or onward to the airport, the fare moves with the kilometres and the "
            f"hours you actually use.",
            "Everything is inside the fare. Tolls, parking, driver service and the wait while your "
            "train unloads are all included. There is no surge multiplier, no meter, and no "
            "cash-on-the-day surprise.",
            "Intercity is the same price as the airport run. A transfer between two cities does not "
            "carry an airport surcharge - the rate you see for one station is the rate you get "
            "between cities.",
        ],
        "both": [
            "Your vehicle sets the base. 4-seat economy sedan for a couple of bags, 4-seat "
            "comfort sedan for a longer road, 6-seat MPV for a family, 8-11 seat van for a group, "
            "up to a 55-seat coach for a delegation.",
            f"Distance and time are measured, not guessed. Whether we collect you from "
            f"{ap_name or 'the airport'} or {rail_name or 'the station'}, the fare moves with the "
            f"kilometres and the hours you actually use.",
            "Everything is inside the fare. Tolls, parking, driver service and free waiting time "
            "are all included. There is no surge multiplier, no meter, and no cash-on-the-day "
            "surprise.",
            "Intercity is the same price as the airport run. City-to-city transfers do not carry an "
            "airport surcharge - the rate you see for the airport is the rate you get between "
            "cities.",
        ],
    }
    has_ap = bool(ap_name)
    has_rail = bool(rail_name) and rail_name != ap_name
    key = "both" if (has_ap and has_rail) else ("airport" if has_ap else "rail")
    bullets = B[key]

    adv = pick_adv(city_en)
    adv_cards = "\n".join(
        f'<div class="adv-card"><div class="adv-icon">{i}</div>'
        f'<h4 class="adv-title">{esc(t)}</h4>'
        f'<p class="adv-body">{esc(b)}</p></div>' for i, t, b in adv)

    rows = "\n".join(
        f'<tr><td><strong>{esc(en)}</strong> <span class="qb-cn">{esc(cn)}</span></td>'
        f'<td class="qb-price">¥{pr}</td>'
        f'<td class="qb-usd">≈ ${round(pr / 7.1, 2)}</td></tr>'
        for en, cn, pr in samples)

    return f"""
{MARK}
 <section class="section pl-section" id="price-list">
 <div class="container">
 <div class="section-header">
 <h2>What Your {esc(title_city)} Ride Will Cost</h2>
 <div class="divider"></div>
 <p class="text-lead">{esc(lead)}</p>
 </div>

 <div class="pl-cols">
  <div class="pl-card">
   <h4 class="pl-card-title">📐 How the price is built</h4>
   <p class="pl-card-sub">One formula, applied to every city. You get the number in writing before you pay
   anything &mdash; and it is the number that is charged.</p>
   <ul class="qb-list">
    <li><strong>Your vehicle sets the base.</strong> {esc(bullets[0])}</li>
    <li><strong>Distance and time are measured, not guessed.</strong> {esc(bullets[1])}</li>
    <li><strong>Everything is inside the fare.</strong> {esc(bullets[2])}</li>
    <li><strong>Intercity is the same price as the airport run.</strong> {esc(bullets[3])}</li>
   </ul>
   <div class="qb-cta">
    <a href="booking.html?city={esc(city_en.replace(' ', '%20'))}" class="btn btn-accent btn-large">Get Your {esc(city_en)} Quote</a>
    <a href="https://wa.me/8615527771775?text=Hi%20Chinawheely%2C%20please%20quote%20my%20{esc(city_en.replace(' ', '%20'))}%20transfer" class="btn btn-outline btn-large" target="_blank" rel="noopener">Ask on WhatsApp</a>
   </div>
   <p class="qb-note">Same-day quotes on WhatsApp &mdash; we reply between 08:00 and 24:00 Beijing time.
   The quote is valid for 48 hours, and you can change or cancel free up to 48 hours before pickup.</p>
  </div>

  <div class="pl-card">
   <h4 class="pl-card-title">📊 Our Published Prices, For Reference</h4>
   <p class="pl-card-sub">These are live, published 2026 rates for the cities on our price list.
   The same formula and the same rules produce your {esc(city_en)} quote &mdash; we are simply
   pricing it for you on request.</p>
   <table class="pl-table qb-table">
    <thead><tr><th>City</th><th>4-seat economy airport transfer</th><th>USD</th></tr></thead>
    <tbody>
{rows}
    </tbody>
   </table>
   <p class="qb-note">Want the full table &mdash; every vehicle class, every hour tier, for all
   53 published cities? It is one click away, and it is the same sheet our drivers are paid from.</p>
   <div class="qb-cta">
    <a href="prices.html" class="btn btn-outline btn-large">See All Published Prices</a>
   </div>
  </div>
 </div>

 <div class="pl-why">
 <div class="pl-why-head">
 <h3 class="pl-title">Why travellers book {esc(city_en)} with Chinawheely</h3>
 <p class="pl-lede">Six things that come with every booking &mdash; in {esc(city_en)} and across
 all 346 cities on the platform.</p>
 </div>
 <div class="adv-grid">
{adv_cards}
 </div>
 </div>

 <div class="pl-cta">
 <div class="pl-cta-copy">
 <h3>Ask once, book with certainty</h3>
 <p>Send us your route and date. You get a written fixed price for every vehicle option, with the
 inclusions spelled out &mdash; then book it in one click and change it free up to 48 hours before pickup.</p>
 </div>
 <div class="pl-cta-actions">
 <a href="booking.html?city={esc(city_en.replace(' ', '%20'))}" class="btn btn-accent btn-large">Get an Instant Quote</a>
 <a href="prices.html" class="btn btn-outline btn-large">Published Price List</a>
 </div>
 </div>
 </div>
 </section>
{END}
"""


def main():
    sys.path.insert(0, os.path.join(BASE, "tools"))
    import apply_quote_blocks as Q
    samples = Q.pick_samples()

    n = 0
    for fn in sorted(os.listdir(BASE)):
        if not fn.endswith(".html"):
            continue
        slug = fn[:-5]
        if slug in SKIP_SLUGS or THEME_PAT.search(slug):
            continue
        p = os.path.join(BASE, fn)
        s = open(p, encoding="utf-8").read()
        if MARK not in s:
            continue
        i = s.find(MARK)
        j = s.find(END, i)
        if j < 0:
            continue
        city_en = Q.city_name_from_html(s)
        if not city_en:
            print("跳过（无城市名）:", fn)
            continue
        block = build_personalized(slug, city_en, samples)
        s = s[:i] + block + s[j + len(END):]
        open(p, "w", encoding="utf-8").write(s)
        n += 1
    print(f"个性化 {n} 页")
    return 0


if __name__ == "__main__":
    sys.exit(main())

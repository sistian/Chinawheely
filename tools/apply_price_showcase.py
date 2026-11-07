#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P5 —— 首页 + 城市页「真实报价 + 优势卖点」展示层

数据源：pricing/pricing.json（唯一真相源，来自更新版报价单 xlsx）
口径：
  * 人民币为主，美元参考，1 USD = 7.10 CNY
  * Intercity 城际 = 接送机同价
  * 有价城市展示完整车型价目表；无价城市展示「实时报价」入口（不编造价格）

本脚本做三件事：
  1. FIX  首页航线价格错位（route-row 逐块匹配，不再用前 700 字符窗口）
  2. FIX  城市页日游卡错按机场价计（应按包车时长档）
  3. ADD  城市页「Transparent Price List」区块（真实价目表 + 优势卖点 + CTA）
  4. ADD  首页「Why Chinawheely」优势卖点区

用法: python3 tools/apply_price_showcase.py [--dry]
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
RATE = data["meta"]["usdCnyRate"]
VEH = {v["key"]: v for v in data["vehicles"]["airport"]}

HOUR_TIER = {2: "2h_35km", 4: "4h_50km", 6: "6h_75km", 8: "8h_100km", 10: "10h_125km"}

# 页面 slug → 价格表 slug
SLUG_ALIAS = {
    "huhehaote": "huhehaote",  # pricing.json 已用站点 slug
}

# 首页具名航线 → 城市 slug（用 IATA 三字码，机场全名会变，三字码稳定）
INDEX_ROUTES = [
    ("Beijing Capital (PEK)", "beijing"),
    ("Shanghai Pudong (PVG)", "shanghai"),
    ("Chengdu Tianfu (TFU)", "chengdu"),
]

# ─────────────────────────────────────────────────────────── 工具
def usd(cny):
    return round(cny / RATE, 2)


def fmt(cny):
    """标准展示格式：From ¥X (≈ $X)"""
    return f"From ¥{cny} (≈ ${usd(cny)})"


def fmt_usd_plain(cny):
    """纯美元展示格式（用于已有 (≈ $X) 括号的老文案）"""
    return f"(≈ ${usd(cny)})"


def city_of(slug):
    return CITIES.get(SLUG_ALIAS.get(slug, slug))


def esc(s):
    """转义文本，但保留 HTML 实体不被二次转义。
    我们自己写的文案里已经用了 &mdash; &yen; &nbsp; 等实体，
    若整体转义会变成 &amp;mdash; 在页面上显示成字面量。"""
    s = html.escape(str(s), quote=False)
    # 把被误转义的实体还原
    for ent in ("mdash", "yen", "nbsp", "amp", "rarr", "lt", "gt", "quot", "apos", "times", "harr"):
        s = s.replace("&amp;" + ent + ";", "&" + ent + ";")
    return s


# ─────────────────────────────────────────── 1. 首页航线价格错位修复
def fix_index_routes():
    """原 bug：idx_repl 用价格前 700 字符窗口匹配航线标签，
    第一条标签会命中后面的价格块，导致 3 条航线价格整体错位一格。
    修法：先把 index 切成一个个 route-row 块，每块内独立匹配。"""
    path = os.path.join(BASE, "index.html")
    if not os.path.exists(path):
        return 0
    s = open(path, encoding="utf-8").read()
    orig = s

    def repl_row(row):
        if "From ¥" not in row:
            return row
        for label, cslug in INDEX_ROUTES:
            if label not in row:
                continue
            c = city_of(cslug)
            if not c:
                continue
            vals = [v["pkg"] for v in c["airport"].values() if v.get("pkg") is not None]
            if not vals:
                continue
            new = fmt(min(vals))
            row = re.sub(r"From ¥[\d,]+(?:\s*\(≈\s*\$[\d.]+\))?", new, row, count=1)
            return row
        return row

    # route-row 块：以下一个 route-row 或非空白字符为界，逐块独立匹配
    parts = re.split(r'(?=<div class="route-row">)', s)
    out = []
    for part in parts:
        if part.startswith('<div class="route-row">'):
            out.append(repl_row(part))
        else:
            out.append(part)
    s = "".join(out)

    if s != orig:
        if not DRY:
            open(path, "w", encoding="utf-8").write(s)
        return 1
    return 0


# ─────────────────────────────────── 2. 城市页日游卡错按机场价修复
def fix_day_trip_pricing():
    """原 bug：日游卡没有明确小时数时回落到「机场接送最低价」，
    导致「City day itinerary」这类全天包车被标成机场价（例：银川 ¥186，
    而 8 小时包车实为 ¥546）。这属于严重低价错报，会直接亏本接单。
    修法：日游/全天/包车语义一律按 8 小时包车档取价。"""
    stats = {"fixed": 0, "pages": 0}
    for fn in sorted(os.listdir(BASE)):
        if not fn.endswith(".html"):
            continue
        path = os.path.join(BASE, fn)
        s = open(path, encoding="utf-8").read()
        if len(s) < 15000:
            continue
        slug = fn[:-5]
        c = city_of(slug)
        if not c:
            continue

        eco = c["airport"]["sedan_economy"]["pkg"]
        ch8 = c["charter"]["sedan_4"]["tiers"]["8h_100km"]["pkg"]
        if eco == ch8:
            continue

        m = re.search(r'Day Trips from [A-Za-z ]*?</h2>(.*?)</section>', s, re.S)
        if not m:
            continue
        seg = m.group(1)
        changed = False

        def repl(mm):
            nonlocal changed
            head, body, price = mm.group(1), mm.group(2), mm.group(3)
            if int(price.replace(",", "")) != eco:
                return mm.group(0)
            txt = re.sub(r"<[^>]+>", " ", body)
            if re.search(r"\d+\s*-?\s*hours?", txt, re.I):
                return mm.group(0)          # 有明确小时数，交给 apply_prices 的档位逻辑
            if not re.search(r"day itinerary|day trip|full-day|full day|day tour|"
                             r"day pass|day-long|daylong", txt, re.I):
                return mm.group(0)          # 不是日游语义
            changed = True
            stats["fixed"] += 1
            return head + body + f"From ¥{ch8} (≈ ${usd(ch8)})"

        new_seg = re.sub(
            r'(<h4[^>]*>.*?</h4>)(.{0,700}?)From ¥([\d,]+)(?:\s*\(≈\s*\$[\d.]+\))?',
            repl, seg, flags=re.S)
        if changed:
            s = s[:m.start(1)] + new_seg + s[m.end(1):]
            stats["pages"] += 1
            if not DRY:
                open(path, "w", encoding="utf-8").write(s)
    return stats


# ───────────────────────────────── 3. 城市页「Transparent Price List」区块
PRICE_BLOCK_MARK = "<!-- CW:PRICE-LIST -->"
PRICE_BLOCK_END = "<!-- /CW:PRICE-LIST -->"

ADVANTAGES = [
    ("🛡️", "Licensed travel agency, not a ride-hail app",
     "Chinawheely is a registered travel agency (L-HUB-101603). Your booking is a "
     "travel contract with a licensed operator — not a broker handing your number to "
     "whoever answers the phone."),
    ("🔒", "One locked price, shown before you pay",
     "The price you see is the price you pay. Tolls, parking, driver service and "
     "airport waiting time are already inside it. No surge pricing, no meter, no "
     "cash-on-the-day surprise."),
    ("✈️", "Flight tracked, waiting time on us",
     "We watch your flight number in real time. If it lands late or is delayed, your "
     "driver shifts with it and the waiting time stays on us — not on your bill."),
    ("🧑‍✈️", "A licensed driver who knows the city",
     "Every car is driven by a professional local driver who knows the routes, the "
     "shortcuts and the parking that actually works near the attractions — with "
     "English communication and a name board on arrival."),
    ("⏱️", "Free changes up to 48 hours before",
     "Plans move. Reschedule or cancel any booking free of charge up to 48 hours "
     "before your scheduled pickup, straight from your confirmation link."),
    ("💬", "A real human on WhatsApp, 8AM–12AM Beijing time",
     "One message reaches a person who can re-price, re-route or re-plan your trip "
     "on the spot. No ticket queue, no chatbot loop."),
]


def build_price_table(c):
    """生成真实价目表 HTML（机场/城际 + 包车）"""
    rows = []
    ap = c["airport"]
    for key in ["sedan_economy", "sedan_comfort", "mpv_6", "van_8_11", "van_12_18", "coach_19_55"]:
        v = ap.get(key)
        if not v or v.get("pkg") is None:
            continue
        rows.append(
            f'<tr><td><strong>{esc(v["name"])}</strong></td>'
            f'<td>{v["seats"]}</td><td>{v["bags"]}</td>'
            f'<td class="pl-price">¥{v["pkg"]}</td>'
            f'<td class="pl-usd">≈ ${usd(v["pkg"])}</td>'
            f'<td class="pl-rate">¥{v["perMin"]}/min · ¥{v["perKm"]}/km</td></tr>')
    ap_rows = "\n".join(rows)

    ch_rows = []
    ch = c["charter"]
    for key in ["sedan_4", "mpv_6", "van_8_11", "van_12_18", "coach_19_55"]:
        v = ch.get(key)
        if not v:
            continue
        tiers = v["tiers"]
        cells = []
        for t in ["2h_35km", "4h_50km", "6h_75km", "8h_100km", "10h_125km"]:
            tv = tiers.get(t)
            cells.append(f'<td class="pl-price">¥{tv["pkg"]}</td>' if tv else "<td>—</td>")
        ch_rows.append(
            f'<tr><td><strong>{esc(v["name"])}</strong></td>'
            + "".join(cells) + "</tr>")
    ch_rows_html = "\n".join(ch_rows)

    return f"""
 <div class="pl-wrap">
  <div class="pl-head">
   <div class="pl-head-copy">
    <h3 class="pl-title">Fixed Price List &mdash; {esc(c['cn'])} ({esc(c['en'])})</h3>
    <p class="pl-lede">Published rates from our 2026 quote sheet. Renminbi first, USD for reference at
    1 USD = &yen;{RATE:.2f}. Every price below already includes tolls, parking, driver service and
    free airport waiting time &mdash; nothing is added on the day.</p>
   </div>
   <div class="pl-badges">
    <span class="pl-badge pl-badge-fix">Fixed price</span>
    <span class="pl-badge">No surge pricing</span>
    <span class="pl-badge">All fees included</span>
   </div>
  </div>

  <div class="pl-cols">
   <div class="pl-card">
    <h4 class="pl-card-title">🛬 Airport &amp; Intercity Transfer</h4>
    <p class="pl-card-sub">One flat fare for airport pickup, drop-off or city-to-city &mdash;
    <strong>intercity costs the same as the airport run</strong>. 35&nbsp;km and 60&nbsp;minutes included; beyond that
    we charge by the minute and the kilometre at the rates shown.</p>
    <table class="pl-table">
     <thead><tr><th>Vehicle</th><th>Seats</th><th>Bags</th><th>Fixed fare</th><th>USD</th><th>Beyond 35 km / 60 min</th></tr></thead>
     <tbody>
{ap_rows}
     </tbody>
    </table>
   </div>

   <div class="pl-card">
    <h4 class="pl-card-title">🚗 Hourly Private Charter</h4>
    <p class="pl-card-sub">Book the car and the hours, keep the car for the day. Unused
    kilometres can be carried into the next tier, so a long day never turns into a
    penalty. The driver stays with you &mdash; you set the stops.</p>
    <table class="pl-table pl-table-charter">
     <thead><tr><th>Vehicle</th><th>2h / 35km</th><th>4h / 50km</th><th>6h / 75km</th><th>8h / 100km</th><th>10h / 125km</th></tr></thead>
     <tbody>
{ch_rows_html}
     </tbody>
    </table>
   </div>
  </div>
 </div>
"""


def build_advantages(city_en):
    cards = []
    for icon, title, body in ADVANTAGES:
        cards.append(
            f'<div class="adv-card"><div class="adv-icon">{icon}</div>'
            f'<h4 class="adv-title">{esc(title)}</h4>'
            f'<p class="adv-body">{esc(body)}</p></div>')
    return "\n".join(cards)


def build_price_section(c):
    """完整的价格区块（价目表 + 优势 + 双 CTA）"""
    city = c["en"]
    return f"""
{PRICE_BLOCK_MARK}
 <section class="section pl-section" id="price-list">
 <div class="container">
 <div class="section-header">
 <h2>Transparent Pricing in {esc(city)}</h2>
 <div class="divider"></div>
 <p class="text-lead">Published rates, no estimate games. Check the numbers yourself before you book &mdash;
 and the price you see is the price your driver is paid from.</p>
 </div>
{build_price_table(c)}
 <div class="pl-why">
 <div class="pl-why-head">
 <h3 class="pl-title">Why travellers book {esc(city)} with Chinawheely</h3>
 <p class="pl-lede">Six things you get with every booking &mdash; in {esc(city)} and across all
 346 cities on the platform.</p>
 </div>
 <div class="adv-grid">
{build_advantages(city)}
 </div>
 </div>
 <div class="pl-cta">
 <div class="pl-cta-copy">
 <h3>Book {esc(city)} at the published price</h3>
 <p>Pick your vehicle, see the fare line by line, and pay by PayPal or Alipay. Free changes up to
 48 hours before pickup &mdash; or ask on WhatsApp and we will hold a car for you.</p>
 </div>
 <div class="pl-cta-actions">
 <a href="booking.html?city={esc(city.replace(' ', '%20'))}" class="btn btn-accent btn-large">Get Your {esc(city)} Price</a>
 <a href="https://wa.me/8615527771775?text=Hi%20Chinawheely%2C%20I%27d%20like%20a%20fixed%20price%20in%20{esc(city.replace(' ', '%20'))}" class="btn btn-outline btn-large" target="_blank" rel="noopener">Ask on WhatsApp</a>
 </div>
 </div>
 </div>
 </section>
{PRICE_BLOCK_END}
"""


def insert_city_price_sections():
    """给所有有价城市页插入真实价目表区块（幂等）"""
    stats = {"pages": 0, "skipped": 0}
    for fn in sorted(os.listdir(BASE)):
        if not fn.endswith(".html"):
            continue
        slug = fn[:-5]
        c = city_of(slug)
        if not c:
            continue
        path = os.path.join(BASE, fn)
        s = open(path, encoding="utf-8").read()
        if len(s) < 15000:
            continue
        if PRICE_BLOCK_MARK in s:
            stats["skipped"] += 1
            continue

        # 锚点：Popular {City} Routes 段落之后
        m = re.search(r'<h2[^>]*>\s*Popular [^<]*Routes\s*</h2>', s)
        if not m:
            stats["skipped"] += 1
            continue
        st = s.rfind("<section", 0, m.start())
        en = s.find("</section>", m.end())
        if st < 0 or en < 0:
            stats["skipped"] += 1
            continue
        ins_at = en + len("</section>")

        block = build_price_section(c)
        s = s[:ins_at] + block + s[ins_at:]
        stats["pages"] += 1
        if not DRY:
            open(path, "w", encoding="utf-8").write(s)
    return stats


# ─────────────────────────────────── 4. 首页「Why Chinawheely」优势区
HOME_ADV_MARK = "<!-- CW:WHY-ADV -->"


def build_home_advantages():
    cards = []
    for icon, title, body in ADVANTAGES:
        cards.append(
            f'<div class="adv-card"><div class="adv-icon">{icon}</div>'
            f'<h4 class="adv-title">{esc(title)}</h4>'
            f'<p class="adv-body">{esc(body)}</p></div>')
    return "\n".join(cards)


def insert_home_advantages():
    path = os.path.join(BASE, "index.html")
    s = open(path, encoding="utf-8").read()
    if HOME_ADV_MARK in s:
        return 0
    # 放在 Transparent Pricing 区块之后
    i = s.find('id="pricing"')
    if i < 0:
        return 0
    j = s.find("</section>", i)
    if j < 0:
        return 0
    at = j + len("</section>")

    block = f"""
{HOME_ADV_MARK}
 <section class="section pl-section" id="why-us">
 <div class="container">
 <div class="section-header">
 <h2>Why Travellers Book Chinawheely</h2>
 <div class="divider"></div>
 <p class="text-lead">Six reasons this is not another app handing your number to a random driver.</p>
 </div>
 <div class="adv-grid">
{build_home_advantages()}
 </div>
 <div class="pl-cta">
 <div class="pl-cta-copy">
 <h3>See your fixed price before you pay anything</h3>
 <p>Published rates on 53 cities, instant quotes on the rest. Pick your vehicle, watch the fare
 build line by line, and pay by PayPal or Alipay &mdash; with free changes up to 48 hours before pickup.</p>
 </div>
 <div class="pl-cta-actions">
 <a href="booking.html" class="btn btn-accent btn-large">Get an Instant Price</a>
 <a href="prices.html" class="btn btn-outline btn-large">See All Published Prices</a>
 </div>
 </div>
 </div>
 </section>
"""
    s = s[:at] + block + s[at:]
    if not DRY:
        open(path, "w", encoding="utf-8").write(s)
    return 1


# ─────────────────────────────────────────────────────────── main
def main():
    print("F1 首页航线价格错位修复：", fix_index_routes(), "个文件")
    st = fix_day_trip_pricing()
    print(f"F2 城市页日游错按机场价修复：{st['fixed']} 处 / {st['pages']} 个文件")
    st2 = insert_city_price_sections()
    print(f"F3 城市页真实价目表区块：新增 {st2['pages']} 页，跳过 {st2['skipped']} 页")
    print("F4 首页优势卖点区：", "已插入" if insert_home_advantages() else "已存在")
    return 0


if __name__ == "__main__":
    sys.exit(main())

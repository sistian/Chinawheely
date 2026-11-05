#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P5b —— 无价城市页的「价格怎么算」区块

无价城市不能编造数字，但可以讲清楚：
  * 价格由什么构成（车型 + 里程 + 时长 + 机场）
  * 为什么值得直接问（比价、免排队、可改期）
  * 怎么拿到价格（一次消息 / 表单）
  * 同时给出「已公布价格的城市」作为参照，让用户信任我们的定价体系

用法: python3 tools/apply_quote_blocks.py
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

MARK = "<!-- CW:QUOTE-BLOCK -->"
END = "<!-- /CW:QUOTE-BLOCK -->"

# 主题页 / 别名桩 / 核心页：不放这个区块
SKIP_SLUGS = {
    "index", "prices", "booking", "contact", "about", "services", "help",
    "terms", "privacy", "careers", "partners", "cookies", "cancellation",
    "404", "manage-order", "thank-you", "admin", "admin-login",
    "seo-swot-analysis", "image_downloader", "batch_download", "get-quote",
    "faq",
}

# 主题页特征（含这些词的页面不做价格区块）
THEME_PAT = re.compile(
    r"(tea-culture|best-time|day-trips|photo-spots|food-shopping|"
    r"airport-transfer-to|detailed|guide)", re.I)


def esc(s):
    s = html.escape(str(s), quote=False)
    for ent in ("mdash", "yen", "nbsp", "amp", "rarr", "lt", "gt", "quot", "apos"):
        s = s.replace("&amp;" + ent + ";", "&" + ent + ";")
    return s


def city_name_from_html(s):
    """从页面标题抽城市名。
    h1 常见形式："Beijing Airport Transfer & Private Car" /
    "Karakax (Hotan) Airport Transfer & Private Car" /
    "Luzhi Jiangnan Water Town Airport Transfer"，
    去掉后缀修饰词，只留城市名（含括号别名）。"""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
    if not m:
        return None
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip()
    # 先切掉主修饰词
    t = re.split(r"\s+(?:Airport|Transfer|Private|Car|Chauffeur|Services?)\b", t)[0]
    # 再切掉景观/别名后缀（Water Town / Hotan 等），保留括号别名形式
    t = re.split(r"\s+(?:Water\s+Town|Jiangnan\s+Water\s+Town)\b", t)[0]
    t = t.strip(" ,-—–&")
    return t or None


def build_quote_block(city_en, city_cn, sample):
    """sample: [(城市EN, 城市CN, 经济型价), ...] —— 已公布价格的城市作参照"""
    rows = "\n".join(
        f'<tr><td><strong>{esc(en)}</strong> <span class="qb-cn">{esc(cn)}</span></td>'
        f'<td class="qb-price">¥{price}</td>'
        f'<td class="qb-usd">≈ ${round(price / RATE, 2)}</td></tr>'
        for en, cn, price in sample)

    return f"""
{MARK}
 <section class="section pl-section" id="price-list">
 <div class="container">
 <div class="section-header">
 <h2>What Your {esc(city_en)} Ride Will Cost</h2>
 <div class="divider"></div>
 <p class="text-lead">{esc(city_en)} is not on our published price list yet &mdash; so we quote it
 for you. Here is exactly how the number is built, and what you get for it.</p>
 </div>

 <div class="pl-cols">
  <div class="pl-card">
   <h4 class="pl-card-title">📐 How the price is built</h4>
   <p class="pl-card-sub">One formula, applied to every city. You get the number in writing before you pay
   anything &mdash; and it is the number that is charged.</p>
   <ul class="qb-list">
    <li><strong>Your vehicle sets the base.</strong> 4-seat economy sedan for a couple of bags,
    4-seat comfort sedan for a longer road, 6-seat MPV for a family, 8&ndash;11 seat van for a group,
    up to a 55-seat coach for a delegation.</li>
    <li><strong>Distance and time are measured, not guessed.</strong> Airport pickup, one-way city
    transfer or a full-day charter &mdash; the fare moves with the kilometres and the hours you
    actually use.</li>
    <li><strong>Everything is inside the fare.</strong> Tolls, parking, driver service and free
    airport waiting time are all included. There is no surge multiplier, no meter, and no
    cash-on-the-day surprise.</li>
    <li><strong>Intercity is the same price as the airport run.</strong> City-to-city transfers do
    not carry an airport surcharge &mdash; the rate you see for the airport is the rate you get
    between cities.</li>
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
   {len(CITIES)} published cities? It is one click away, and it is the same sheet our drivers are paid from.</p>
   <div class="qb-cta">
    <a href="prices.html" class="btn btn-outline btn-large">See All Published Prices</a>
   </div>
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


def pick_samples():
    """挑选已公布价格的城市作参照（取中位价附近 + 几个代表城市）"""
    items = [(c["en"], c["cn"], c["airport"]["sedan_economy"]["pkg"])
             for c in CITIES.values()
             if c.get("airport", {}).get("sedan_economy", {}).get("pkg") is not None]
    items.sort(key=lambda x: x[2])
    n = len(items)
    picks = []
    # 最低价、中位、最高价 + 几个知名城市
    for target in [items[0], items[n // 2], items[-1]]:
        if target not in picks:
            picks.append(target)
    for name in ["Beijing", "Shanghai", "Guangzhou", "Chengdu", "Shenzhen", "Hangzhou"]:
        for it in items:
            if it[0] == name and it not in picks:
                picks.append(it)
                break
    picks = picks[:8]
    picks.sort(key=lambda x: x[2])
    return picks


def main():
    samples = pick_samples()
    stats = {"added": 0, "skipped": 0, "skip_no_price": 0}
    for fn in sorted(os.listdir(BASE)):
        if not fn.endswith(".html"):
            continue
        slug = fn[:-5]
        if slug in SKIP_SLUGS or THEME_PAT.search(slug):
            stats["skipped"] += 1
            continue
        p = os.path.join(BASE, fn)
        s = open(p, encoding="utf-8").read()
        if len(s) < 15000:
            stats["skipped"] += 1
            continue
        if MARK in s:
            stats["skipped"] += 1
            continue
        if "<!-- CW:PRICE-LIST -->" in s:
            stats["skipped"] += 1     # 已有真实价目表
            continue
        if re.search(r"This page has moved", s, re.I):
            stats["skipped"] += 1     # 别名桩页
            continue

        city_en = city_name_from_html(s)
        if not city_en:
            stats["skipped"] += 1
            continue
        city_cn = ""
        m = re.search(r'"name":\s*"([^"]+)"', s)
        if m:
            city_cn = m.group(1)

        m = re.search(r'<h2[^>]*>\s*Popular [^<]*Routes\s*</h2>', s)
        if not m:
            stats["skipped"] += 1
            continue
        st = s.rfind("<section", 0, m.start())
        en = s.find("</section>", m.end())
        if st < 0 or en < 0:
            stats["skipped"] += 1
            continue
        at = en + len("</section>")

        # 确认这是无价城市（路由卡是 Quote on request）
        near = s[m.start():at]
        if "Quote on request" not in near:
            stats["skip_no_price"] += 1
            continue

        block = build_quote_block(city_en, city_cn, samples)
        s = s[:at] + block + s[at:]
        stats["added"] += 1
        if not DRY:
            open(p, "w", encoding="utf-8").write(s)
    print(f"新增报价区块 {stats['added']} 页，跳过 {stats['skipped']} 页，"
          f"非无价页 {stats['skip_no_price']} 页")
    return 0


if __name__ == "__main__":
    sys.exit(main())

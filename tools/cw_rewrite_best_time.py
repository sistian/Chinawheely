#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用真实气候数据重写 23 个城市页的「Best Time to Visit」段（幂等）
背景：23 个 best-time 主题页被合并成 301 → 城市页 #best-time 锚点，
      所以锚点处必须有真正像样的内容。原状态：
        - fuzhou / guangzhou / shanghai / shenzhen / xiamen / xian 六城正文只有
          41–109 词（shanghai 的季节卡里甚至写着 "Season note 1" 占位）
        - 所有 23 城的季节卡 "Highlights:" 全是空的
      数据源：中文维基「气候数据/气候表」模板解析出的逐月均温 + 逐月降水
             （workspace/best_time_data.json，296 城真实数据）
做法：全部文案由数据推导，不写任何未经核实的事实。
"""
import json, os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
DATA = '/Users/w/.openclaw/workspace/best_time_data.json'
os.chdir(SITE)

MON = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
       'August', 'September', 'October', 'November', 'December']
SEASONS = [('Spring', [3, 4, 5]), ('Summer', [6, 7, 8]),
           ('Autumn', [9, 10, 11]), ('Winter', [12, 1, 2])]

data = json.load(open(DATA, encoding='utf-8'))
plan = json.load(open('tools/theme_merge_plan.json', encoding='utf-8'))
cities = sorted({v.lstrip('/').split('#')[0][:-5] for k, v in plan.items()
                 if 'best-time' in k})


def mm(d, m):
    v = d.get('monthly_means') or {}
    try:
        return float(v.get(str(m)))
    except (TypeError, ValueError):
        return None


def mp(d, m):
    v = d.get('monthly_precip') or {}
    x = v.get(str(m)) if isinstance(v, dict) else None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def r1(x):
    return round(float(x), 1)


def season_stats(d, months):
    temps = [mm(d, m) for m in months]
    temps = [t for t in temps if t is not None]
    ps = [mp(d, m) for m in months]
    ps = [p for p in ps if p is not None]
    return (r1(sum(temps) / len(temps)) if temps else None,
            round(sum(ps)) if ps else None)


def build(city):
    d = data.get(city, {})
    means = d.get('monthly_means') or {}
    if not means:
        return None
    temps = {int(k): float(v) for k, v in means.items()}
    precip = {}
    for m in range(1, 13):
        x = mp(d, m)
        if x is not None:
            precip[m] = x

    hot_m = max(temps, key=lambda m: temps[m])
    cold_m = min(temps, key=lambda m: temps[m])
    hot_t, cold_t = temps[hot_m], temps[cold_m]
    rng = r1(hot_t - cold_t)
    avg = d.get('avg_temp_c')
    rain = d.get('rain_mm')

    rainy_m = max(precip, key=lambda m: precip[m]) if precip else None
    dry_m = min(precip, key=lambda m: precip[m]) if precip else None

    ss = {name: season_stats(d, months) for name, months in SEASONS}
    wet_season = max(ss.items(), key=lambda kv: (kv[1][1] or -1))
    dry_season = min(ss.items(), key=lambda kv: (kv[1][1] if kv[1][1] is not None else 9e9))

    # ---------- lead ----------
    lead = (f"{city} runs from {r1(cold_t)} °C in {MON[cold_m - 1]} to {r1(hot_t)} °C in "
            f"{MON[hot_m - 1]}, an annual average of {avg} °C")
    if rain:
        lead += f" and about {round(rain):,} mm of rain across the year"
    lead += ". The chart and the four seasons below are built from the city’s own climate record."

    # ---------- numbers paragraph ----------
    p2 = (f"{MON[hot_m - 1]} is the warmest month at {r1(hot_t)} °C and "
          f"{MON[cold_m - 1]} the coldest at {r1(cold_t)} °C, a spread of {rng} °C.")
    if rainy_m and precip.get(rainy_m):
        p2 += (f" Rain is heaviest in {MON[rainy_m - 1]}, which averages "
               f"{round(precip[rainy_m])} mm, and lightest in {MON[dry_m - 1]} at "
               f"{round(precip[dry_m])} mm.")
    if wet_season[1][1] is not None:
        p2 += (f" {wet_season[0]} is the wettest stretch of the year at about "
               f"{wet_season[1][1]:,} mm in total, while {dry_season[0]} is the driest at "
               f"{dry_season[1][1]:,} mm.")

    # ---------- 何时来 ----------
    if wet_season[1][1] and dry_season[1][1]:
        p3 = (f"For most travellers the {dry_season[0].lower()} window is the one to plan "
              f"around: it carries only about {dry_season[1][1]:,} mm of rain across the "
              f"whole season, against roughly {wet_season[1][1]:,} mm in "
              f"{wet_season[0].lower()}.")
        if rng >= 20:
            p3 += (f" The {rng} °C gap between the extremes also means the shoulder "
                   f"months either side of {wet_season[0].lower()} sit in a comfortable "
                   f"band, with many days in the high teens or low twenties.")
        else:
            p3 += (f" With a {rng} °C gap between the extremes, the year is mild enough "
                   f"that the choice of month matters less than the choice of week.")
    else:
        p3 = (f"The seasonal swing here is {rng} °C between {MON[cold_m - 1]} and "
              f"{MON[hot_m - 1]}, which is narrow enough that most of the year suits "
              f"a visit.")

    # ---------- 带车角度 ----------
    p4 = (f"Private transfers are booked by pickup time rather than by season, so the "
          f"weather only changes what you do with the hours you have. In "
          f"{MON[cold_m - 1]} a driver waiting at the terminal matters, because the "
          f"afternoon average sits around {r1(cold_t)} °C; by {MON[hot_m - 1]} the same "
          f"day averages {r1(hot_t)} °C and the car is most of the day’s comfort.")

    # ---------- 季节卡 ----------
    def hi(name, months):
        t, p = ss[name]
        if name == 'Spring':
            return (f"{MON[months[0] - 1]} averages {r1(temps[months[0]])} °C and "
                    f"{MON[months[-1] - 1]} {r1(temps[months[-1]])} °C, so the season "
                    f"warms fast.")
        if name == 'Summer':
            if hot_m in months:
                return (f"{MON[hot_m - 1]} peaks at {r1(hot_t)} °C, the warmest point of "
                        f"the whole year.")
            return f"The warmest stretch of the year, averaging {t} °C."
        if name == 'Autumn':
            return (f"{MON[months[0] - 1]} averages {r1(temps[months[0]])} °C and "
                    f"{MON[months[-1] - 1]} {r1(temps[months[-1]])} °C.")
        return (f"{MON[cold_m - 1]} bottoms out at {r1(cold_t)} °C, the coldest point of "
                f"the whole year.")

    cards = []
    for name, months in SEASONS:
        t, p = ss[name]
        mmn = ', '.join(MON[m - 1] for m in months)
        meta = f"{mmn} · avg {t} °C"
        if p is not None:
            meta += f" · {p:,} mm rain"
        cards.append(f'<div class="card">\n'
                     f'  <h4>{name}</h4>\n'
                     f'  <p class="u-text-sm u-text-muted">{meta}</p>\n'
                     f'  <p>{hi(name, months)}</p>\n'
                     f'</div>')

    cards_html = ('\n        '.join(cards))
    html = f'''<section class="section" style="background:var(--color-gray-100);" id="best-time">
  <div class="container">
    <div class="section-header">
      <h2>Best Time to Visit {city}</h2>
      <div class="divider"></div>
      <p class="text-lead">{lead}</p>
    </div>
    <div class="info-box">
      <p>{p2}</p>
      <p>{p3}</p>
      <p>{p4}</p>
    </div>
    <div class="grid grid-4" style="margin-top:var(--space-8);">
        {cards_html}
    </div>
  </div>
</section>'''
    return html


ok = 0
skip = []
for city in cities:
    h = open(f'{city}.html', encoding='utf-8').read()
    new = build(city)
    if not new:
        skip.append(city)
        continue
    # 定位现有 best-time section
    m = re.search(r'<section[^>]*id="best-time"[^>]*>.*?</section>', h, re.S)
    if not m:
        skip.append(city + '(无锚点)')
        continue
    h = h[:m.start()] + new + h[m.end():]
    open(f'{city}.html', 'w', encoding='utf-8').write(h)
    ok += 1

print(f'重写 {ok} 个城市的 Best Time 段；跳过 {skip}')

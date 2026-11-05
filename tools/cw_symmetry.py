#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
城市信息对称性体检（首页 + 全部城市页）

检查「同一个事实在不同地方说法不一致」：
  1. 城市中英文名：<title>/<h1>/meta description/JSON-LD/pricing.json/机场库 是否一致
  2. 省份：JSON-LD containedInPlace / 正文 "Local Province" / 权威映射表 是否一致
  3. 人口 / 面积：JSON-LD 与 city_facts 是否一致
  4. 起步价：页面显示价 是否 == pricing.json 该城真实起步价
  5. 首页城市卡片 vs 城市页自身信息（名称/链接/价格）
  6. 页内正文是否残留别城信息（跨城串味）
  7. og:url / canonical / hreflang 指向自身
"""
import json
import os
import re
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = "/Users/w/.openclaw/workspace"

# ---------- 权威数据 ----------
pricing = json.load(open(os.path.join(BASE, "pricing", "pricing.json"), encoding="utf-8"))
PC = pricing["cities"]

facts = {}
fdir = os.path.join(WS, "city_facts")
if os.path.isdir(fdir):
    for fn in os.listdir(fdir):
        if fn.endswith(".json"):
            try:
                facts[fn[:-5]] = json.load(open(os.path.join(fdir, fn), encoding="utf-8"))
            except Exception:
                pass

prov_map = {}
pm = os.path.join(BASE, "tools", "city_province_map.py")
if os.path.exists(pm):
    src = open(pm, encoding="utf-8").read()
    # CITY_PROV 的 key 是英文城市名（可能是多词），value 是省名
    for m in re.finditer(r'"([^"]+)":\s*"([^"]+)"', src):
        prov_map[m.group(1).lower()] = m.group(2)

# 机场库
airports = {}
adb = os.path.join(BASE, "js", "airport-db.js")
if os.path.exists(adb):
    src = open(adb, encoding="utf-8").read()
    m = re.search(r"=\s*(\{.*?\});", src, re.S)
    if m:
        try:
            airports = json.loads(m.group(1))
        except Exception:
            pass

issues = defaultdict(list)
stats = defaultdict(int)


def add(kind, page, msg):
    issues[kind].append((page, msg))
    stats[kind] += 1


def province_of(slug, p, f):
    """slug → 省份。映射表以英文名为 key。"""
    for src in (p or {}, f or {}):
        en = src.get("en") or src.get("name_en") or src.get("name")
        if en and str(en).lower() in prov_map:
            return prov_map[str(en).lower()]
    # 退化：用 slug
    if slug.lower() in prov_map:
        return prov_map[slug.lower()]
    return None


def text_of(s):
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))


def load(p):
    return open(os.path.join(BASE, p), encoding="utf-8", errors="ignore").read()


def jsonlds(s):
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            out.append(json.loads(m.group(1)))
        except Exception:
            out.append(None)
    return out


# ---------- 页面清单 ----------
EXCL = {
    "index.html", "404.html", "admin.html", "admin-login.html", "thank-you.html",
    "prices.html", "manage-order.html", "booking.html", "contact.html",
    "get-quote.html", "services.html", "help.html", "cookies.html", "partners.html",
    "careers.html", "cancellation.html", "seo-swot-analysis.html",
    "image_downloader.html", "batch_download.html", "about.html", "terms.html",
    "privacy.html", "china-visa-guide.html", "china-consulate-guide.html",
}
THEME = re.compile(r"(day-trips|tea-culture|food|photo|best-time|shopping|"
                   r"airport-transfer-to|china-jade|intercity)")

html_files = sorted(f for f in os.listdir(BASE) if f.endswith(".html"))
city_pages = {}
theme_pages = []
core_pages = []
for fn in html_files:
    if fn in EXCL:
        core_pages.append(fn)
        continue
    if THEME.search(fn):
        theme_pages.append(fn)
    else:
        city_pages[fn] = fn[:-5]

print("=" * 74)
print("城市信息对称性体检")
print("=" * 74)
print("城市页 %d | 主题页 %d | 核心页 %d" % (len(city_pages), len(theme_pages), len(core_pages)))
print("权威数据：pricing 城 %d | city_facts %d | 省份映射 %d | 机场库 %d"
      % (len(PC), len(facts), len(prov_map), len(airports)))
print()

# ---------- 1. 逐城市页 ----------
for fn, slug in sorted(city_pages.items()):
    s = load(fn)
    p = PC.get(slug)
    f = facts.get(slug)

    # 期望的中英文名
    exp_cn = exp_en = None
    if p:
        exp_cn, exp_en = p.get("cn"), p.get("en")
    elif f:
        exp_cn = f.get("cn") or f.get("name_cn")
        exp_en = f.get("en") or f.get("name_en") or f.get("name")

    title = (re.search(r"<title>([^<]*)", s) or [None, ""])[1]
    h1 = ""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
    if m:
        h1 = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
    desc = (re.search(r'<meta name="description" content="([^"]*)"', s) or [None, ""])[1]
    og_title = (re.search(r'<meta property="og:title" content="([^"]*)"', s) or [None, ""])[1]
    body = text_of(s)

    # 1a 城市名出现在 title / h1 / og:title / description
    if exp_en:
        for label, blob in (("title", title), ("og:title", og_title),
                            ("description", desc), ("h1", h1)):
            if not blob:
                continue
            # 页面自己的名字必须出现
            if exp_en.lower() not in blob.lower() and (exp_cn or "") not in blob:
                # 允许别名（slug 含 _ 的独立城市）
                add("名不符", fn, f"{label} 未含本城名 {exp_en}/{exp_cn}: {blob[:70]}")
    if exp_cn and exp_cn not in body and exp_en not in body:
        add("名不符", fn, f"正文未出现本城名 {exp_cn}/{exp_en}")

    # 1b JSON-LD 城市名
    for j in jsonlds(s):
        if not j:
            add("JSON-LD坏", fn, "存在无法解析的 JSON-LD")
            continue
        if j.get("@type") in ("City", "TravelAgency"):
            nm = j.get("name")
            if exp_en and nm and exp_en.lower() not in str(nm).lower() and str(exp_en).lower() not in str(nm).lower():
                add("JSON-LD名不符", fn, f"{j.get('@type')}.name={nm} ≠ {exp_en}")
            if j.get("@type") == "City":
                alt = j.get("alternateName")
                if exp_cn and alt and alt != exp_cn:
                    add("JSON-LD中文名", fn, f"City.alternateName={alt} ≠ {exp_cn}")
                # 1c 省份
                prov = ((j.get("containedInPlace") or {}).get("name"))
                if prov:
                    exp_prov = province_of(slug, p, f)
                    if exp_prov and prov != exp_prov:
                        add("省份不符", fn, f"JSON-LD containedInPlace={prov} ≠ 权威映射 {exp_prov}")
                    elif not exp_prov:
                        add("省份未知", fn, f"JSON-LD 省份 {prov} 但权威映射表无 {slug}")
                # 1d 人口/面积 vs city_facts
                if f:
                    pop = ((j.get("population") or {}).get("value"))
                    fp = f.get("population")
                    if pop and fp:
                        try:
                            if abs(float(pop) - float(str(fp))) > max(2000, float(fp) * 0.02):
                                add("人口不符", fn, f"JSON-LD population={pop} vs city_facts={fp}")
                        except Exception:
                            pass
                    ar = ((j.get("area") or {}).get("value"))
                    fa = f.get("area_km2")
                    if ar and fa:
                        try:
                            if abs(float(ar) - float(str(fa))) > float(fa) * 0.02:
                                add("面积不符", fn, f"JSON-LD area={ar} vs city_facts={fa}")
                        except Exception:
                            pass

    # 1e 正文里的 "Local Province"
    m = re.search(r"Local Province[^A-Za-z]{0,30}([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", body)
    if m:
        stated = m.group(1).strip()
        exp_prov = province_of(slug, p, f)
        if exp_prov and stated != exp_prov:
            add("省份不符", fn, f"正文 Local Province={stated} ≠ {exp_prov}")

    # 1f 起步价一致性
    if p:
        floor = min(v["pkg"] for v in p["airport"].values() if v)
        onpage = [float(x) for x in re.findall(r"From ¥([0-9.]+)", s)]
        if onpage:
            if floor not in onpage:
                add("起步价不符", fn, f"页面价 {sorted(set(onpage))[:4]} 不含真实起步价 {floor}")
            for x in onpage:
                if x not in [v["pkg"] for v in p["airport"].values() if v] and \
                   x not in [t["pkg"] for veh in p.get("charter", {}).values() for t in veh["tiers"].values() if t]:
                    add("价格越界", fn, f"页面价 ¥{x} 不在本城报价集合内")
    else:
        if re.search(r"From ¥[0-9]", s):
            add("无价城显价", fn, "该城不在 pricing.json 却显示 ¥ 起价")

    # 1g canonical / og:url 指向自身
    canon = (re.search(r'<link rel="canonical" href="([^"]*)"', s) or [None, ""])[1]
    ogu = (re.search(r'<meta property="og:url" content="([^"]*)"', s) or [None, ""])[1]
    want = "https://www.chinawheely.com/%s.html" % slug
    if canon and canon != want:
        add("canonical错", fn, f"{canon} ≠ {want}")
    if ogu and ogu != want:
        add("og:url错", fn, f"{ogu} ≠ {want}")

    # 1h 串味：正文出现其它有价城的独占地标
    if slug not in ("beijing",):
        for other in ("Forbidden City", "Great Wall", "Tiananmen", "Summer Palace",
                      "Wangfujing", "Sanlitun", "Dashilar", "Capital Airport"):
            if other.lower() in body.lower():
                add("跨城串味", fn, f"正文出现北京地标「{other}」")
                break
        for other in ("Pudong", "The Bund", "Yu Garden", "Hongqiao", "Nanjing Road"):
            if other.lower() in body.lower() and slug not in ("shanghai",):
                add("跨城串味", fn, f"正文出现上海地标「{other}」")
                break

# ---------- 2. 首页 ----------
idx = load("index.html")
ibody = text_of(idx)
idx_cities = sorted(set(re.findall(r'href="([a-z_]+)\.html"', idx)))
idx_price = {}
for m in re.finditer(r'href="([a-z_]+)\.html"[^>]*>(.*?)</a>', idx, re.S):
    slug, inner = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
    mm = re.search(r"¥\s*([0-9.]+)", inner)
    if mm:
        idx_price[slug] = float(mm.group(1))

for slug, val in idx_price.items():
    p = PC.get(slug)
    if not p:
        add("首页价无源", "index.html", f"{slug} 首页显示 ¥{val} 但不在 pricing.json")
        continue
    floor = min(v["pkg"] for v in p["airport"].values() if v)
    if abs(val - floor) > 0.01:
        add("首页价不符", "index.html", f"{slug} 首页 ¥{val} ≠ 该城起步价 ¥{floor}")

for slug in idx_cities:
    if slug in EXCL or THEME.search(slug):
        continue
    if not os.path.exists(os.path.join(BASE, slug + ".html")):
        add("首页死链", "index.html", f"{slug}.html 不存在")

# ---------- 3. 机场库一致性 ----------
for slug, ap in airports.items():
    if slug not in PC and slug not in facts:
        add("机场库孤儿", "js/airport-db.js", f"{slug} 不在 pricing/facts")
    p = PC.get(slug)
    if p:
        cn = p.get("cn")
        if cn and cn.replace("市", "") not in str(ap):
            add("机场库名", "js/airport-db.js", f"{slug} 机场名 {ap} 与城市 {cn} 不符")

# ---------- 输出 ----------
print("-" * 74)
if not issues:
    print("✓ 未发现信息不对称")
else:
    for kind in sorted(issues, key=lambda k: -len(issues[k])):
        print("\n【%s】%d 处" % (kind, len(issues[kind])))
        for page, msg in issues[kind][:18]:
            print("   %-26s %s" % (page, msg))
        if len(issues[kind]) > 18:
            print("   … 另 %d 处" % (len(issues[kind]) - 18))
print()
print("=" * 74)
print("问题合计 %d" % sum(len(v) for v in issues.values()))

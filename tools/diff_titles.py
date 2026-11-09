#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1 标题差异化 + 目录（TOC）
 1) 通用章节标题 → 注入本页实体（城市/主题）→ 跨城不再一字不差
 2) 站点框架 / 卖点条类标题 → 转非标题元素 <p class="lvl-hN">，移出文档大纲
 3) H2 数 ≥ 6 的页面 → 顶部自动目录（TOC 锚点链到各 H2）
用法: python3 tools/diff_titles.py <site: cw|vip|cwg> [--dry]
"""
import re
import os
import sys
import json
import html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FACTS = "/Users/w/.openclaw/workspace/city_facts"

HRE = re.compile(r"(?is)<h([1-6])\b([^>]*)>(.*?)</h\1\s*>")
TAGRE = re.compile(r"(?s)<[^>]+>")
SKIP = re.compile(r"(?is)<(script|style|noscript|template)\b[^>]*>.*?</\1\s*>")
SUFFIX = re.compile(r"-(day-trips|tea-culture|photo-spots|food-shopping|best-time|travel-tips|"
                     r"nightlife|art-galleries|science-museums|concerts-and-shows|how-to-get-to|"
                     r"zodiac-travel|detailed|walking-tours)$")

# ── 每站规则 ───────────────────────────────────────────────
# demote: 标题文本 → 转非标题（站点框架 / 卖点条）
# rename: 标题文本 → 新标题模板（{E}=实体）
RULES = {
    "cw": {
        "demote": [
            "More China destinations", "Popular destinations", "Chat on WhatsApp",
            "Mobile Pocket Wi-Fi", "One locked price, shown before you pay",
            "Flight tracked, waiting time on us", "A licensed driver who knows the city",
            "Free changes up to 48 hours before", "A real human on WhatsApp",
            "Licensed travel agency, not a ride-hail app", "Start at the landmark",
        ],
        "rename": {
            "Seasons Overview": "{E} Seasons Overview",
            "What the transfer costs": "What the transfer costs in {E}",
            "What to eat": "What to eat in {E}",
            "Where to shop": "Where to shop in {E}",
            "The tea": "The tea in {E}",
            "Teahouses": "Teahouses in {E}",
            "Travel Essentials for Your China Trip": "{E} Travel Essentials",
            "Book a Car in China": "Book a Car in {E}",
            "Tea Ceremony Experience": "Tea Ceremony Experience in {E}",
            "Where the Tea Comes From": "Where the Tea Comes From in {E}",
            "Name Origin": "Name Origin of {E}",
            "Education & Universities": "{E} Education & Universities",
            "Getting Around": "Getting Around {E}",
            "Natural Resources & Environment": "{E} Natural Resources & Environment",
            "Tea Culture": "Tea Culture in {E}",
            "Airport & Intercity Transfer (package includes 35 km + 60 mi)":
                "{E} Airport & Intercity Transfer Rates",
            "Hourly Charter (hours / distance included)": "{E} Hourly Charter Rates",
            "Railway Stations": "{E} Railway Stations",
            "Airports": "{E} Airports",
            "Frequently Asked Questions": "Frequently Asked Questions: Booking in {E}",
            "Prices Hourly Charter Rates": "{E} Published Transfer & Charter Prices",
            "Metro & Transportation": "{E} Metro & Transportation",
            "Maps & Transit": "{E} Maps & Transit",
            "Airport & Intercity Transfer": "{E} Airport & Intercity Transfer Rates",
            "Hourly Charter Rates": "{E} Hourly Charter Rates",
        },
        "toc": True,
    },
    "cwg": {
        "demote": ["Pocket WiFi for China", "Add WhatsApp Customer Service",
                   "English-Speaking Guide", "Medical & Wellness"],
        "rename": {
            "Popular Routes": "Popular Routes from {E}",
            "Food & Dining": "Food & Dining in {E}",
            "Shopping": "Shopping in {E}",
            "Local Vibe & Fun Facts": "{E} Local Vibe & Fun Facts",
            "Speak Like a Local": "Speak Like a Local in {E}",
            "Famous People": "Famous People from {E}",
            "Gallery": "{E} Gallery",
            "Area & Population": "{E} Area & Population",
            "Name Origin": "Name Origin of {E}",
            "Happiness Index": "{E} Happiness Index",
            "Metro & Transport": "Metro & Transport in {E}",
            "Universities": "Universities in {E}",
            "Natural Resources": "Natural Resources in {E}",
        },
        "toc": True,
    },
    "vip": {
        "demote": ["Friendly Links", "Related Theme Pages"],
        "rename": {
            "Entry Reservation": "Entry Reservation in {E}",
            "Travel Essentials for Your China Trip": "{E} Travel Essentials",
            "Practical Information": "Practical Information for {E}",
        },
        "toc": True,
    },
}


def norm(t):
    """规范化：去实体转义、去前导 emoji/符号、压缩空白（用于规则匹配）"""
    s = html.unescape(t)
    s = re.sub(r"^[^\w(（]+", "", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def prefix_of(t):
    """取出标题的前导 emoji/符号"""
    m = re.match(r"^([^\w]+)", t)
    return m.group(1) if m else ""


def load_facts():
    m = {}
    if os.path.isdir(FACTS):
        for f in os.listdir(FACTS):
            if not f.endswith(".json"):
                continue
            try:
                d = json.load(open(os.path.join(FACTS, f), encoding="utf-8"))
            except Exception:
                continue
            slug = os.path.splitext(f)[0]
            m[slug] = {"en": d.get("city_en") or slug.title(),
                       "cn": d.get("city_cn"), "airport": d.get("airport"),
                       "railway": d.get("railway"), "landmark": d.get("landmark_en")}
    return m


FACTS_MAP = load_facts()


STOP = {"best", "how", "top", "popular", "cheap", "the", "a", "an", "what", "why", "when",
        "where", "private", "book", "your", "guide", "travel", "china", "day", "trip"}


def entity_of(relpath, site, h1_text=""):
    raw = os.path.splitext(os.path.basename(relpath))[0]
    if site == "cwg":
        base = re.sub(r"^city-", "", raw)
        topic = False
    else:
        topic = bool(SUFFIX.search(raw))
        base = SUFFIX.sub("", raw)
    base = base.split("_")[0]
    base = re.sub(r"-(city|guide|tour|transfer)$", "", base)
    f = FACTS_MAP.get(base)
    if f and f.get("en"):
        return f["en"], True
    if topic:                      # 主题页用 slug 首词
        return base.replace("-", " ").title(), True
    # 城市页：事实表缺失 → 从 H1 提取专名
    m = re.match(r"^([A-Z][A-Za-z'’\-]+)", h1_text.strip())
    if m and m.group(1).lower() not in STOP:
        return m.group(1), True
    return base.replace("-", " ").title(), False


def slug_id(text):
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return "toc-" + s[:60]


def swap_text(inner, old, new):
    """在标题 inner 的第一个匹配文本节点里把 old 换成 new（处理 &amp; 等实体）"""
    parts = re.split(r"(<[^>]+>)", inner)
    new_esc = html.escape(new, quote=False)
    old_plain = html.unescape(old)
    for i in range(0, len(parts), 2):
        seg = parts[i]
        if not seg:
            continue
        plain = html.unescape(seg)
        if old_plain in plain:
            for cand in (html.escape(old_plain, quote=False), old_plain):
                if cand in seg:
                    parts[i] = seg.replace(cand, new_esc, 1)
                    break
            else:
                parts[i] = plain.replace(old_plain, new_esc, 1)
            return "".join(parts)
    return None


def build_toc(items):
    lis = "".join('<li><a href="#%s">%s</a></li>' % (i, html.escape(t)) for i, t in items)
    return ('<nav class="toc" aria-label="On this page">'
            '<p class="toc-title">On this page</p><ul>%s</ul></nav>' % lis)


def process(html_text, relpath, site, cfg):
    st = {"renamed": 0, "demoted": 0, "toc": 0}
    masked = SKIP.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), html_text)
    h1_text = ""
    mh = re.search(r"(?is)<h1\b[^>]*>(.*?)</h1\s*>", masked)
    if mh:
        h1_text = re.sub(r"\s+", " ", TAGRE.sub(" ", mh.group(1))).strip()
    ent, has_entity = entity_of(relpath, site, h1_text)
    fspans = [(m.start(), m.end()) for m in re.finditer(r"(?is)<footer\b[^>]*>.*?</footer\s*>", masked)]

    def in_footer(pos):
        return any(a <= pos < b for a, b in fspans)

    ms = list(HRE.finditer(masked))
    demote_map = {norm(x): x for x in cfg["demote"]}
    rename_map = {norm(x): v for x, v in cfg["rename"].items()}
    # 第一遍：算新标题文本
    texts = []
    for m in ms:
        t = re.sub(r"\s+", " ", TAGRE.sub(" ", m.group(3))).strip()
        texts.append(t)
    newtexts = list(texts)
    for i, m in enumerate(ms):
        if in_footer(m.start()):
            continue
        t = texts[i]
        k = norm(t)
        if k in demote_map:
            newtexts[i] = None
        elif k in rename_map and has_entity:
            nt = rename_map[k].replace("{E}", ent)
            pfx = prefix_of(t)
            if pfx and not nt.startswith(pfx):
                nt = pfx + " " + nt
            newtexts[i] = nt

    # 第二遍：H2 收集 + 加 id
    h2_items = []
    repl = []
    for i, m in enumerate(ms):
        if in_footer(m.start()):
            continue
        lv = int(m.group(1))
        nt = newtexts[i]
        if nt is None:                       # → 非标题元素
            attrs = m.group(2) or ""
            cm = re.search(r'(?i)\bclass\s*=\s*"([^"]*)"', attrs)
            cls = (cm.group(1) if cm else "")
            if "lvl-h%d" % lv not in cls.split():
                cls = (cls + " lvl-h%d" % lv).strip()
            new_attrs = attrs
            if cm:
                new_attrs = attrs[:cm.start(1)] + cls + attrs[cm.end(1):]
            else:
                new_attrs = attrs.rstrip() + ' class="%s"' % cls
            repl.append((m.start(), m.end(), "<p%s>%s</p>" % (new_attrs, m.group(3))))
            st["demoted"] += 1
            continue
        if nt != texts[i]:
            inner = m.group(3)
            ni = swap_text(inner, texts[i], nt)
            if ni is None:
                ni = inner
            else:
                st["renamed"] += 1
                texts[i] = nt
            repl.append((m.start(), m.end(), "<h%d%s>%s</h%d>" % (lv, m.group(2) or "", ni, lv)))
        if lv == 2 and cfg["toc"]:
            h2_items.append((slug_id(texts[i]), texts[i]))

    # TOC：H2 ≥ 6
    if cfg["toc"] and len(h2_items) >= 6 and '<nav class="toc"' not in html_text:
        toc = build_toc(h2_items)
        # 插到第一个 H2 之前
        first_h2 = None
        for i, m in enumerate(ms):
            if not in_footer(m.start()) and int(m.group(1)) == 2 and newtexts[i] is not None:
                first_h2 = m
                break
        if first_h2:
            repl.append((first_h2.start(), first_h2.start(), toc))
            st["toc"] = 1
            # 给 H2 加 id（替换开标签）
            for i, m in enumerate(ms):
                if in_footer(m.start()) or int(m.group(1)) != 2:
                    continue
                t = texts[i]
                attrs = m.group(2) or ""
                if re.search(r'(?i)\bid\s*=', attrs):
                    continue
                tagend = masked.find(">", m.start())
                if tagend < 0:
                    continue
                aid = slug_id(t)
                newtag = '<h2 id="%s"%s>' % (aid, attrs)
                repl.append((m.start(), tagend + 1, newtag))

    if not repl:
        return html_text, st
    repl.sort(key=lambda x: x[0])
    out, pos = [], 0
    for a, b, r in repl:
        if a < pos:
            continue
        out.append(html_text[pos:a])
        out.append(r)
        pos = b
    out.append(html_text[pos:])
    return "".join(out), st


def main():
    site = sys.argv[1]
    dry = "--dry" in sys.argv
    cfg = RULES[site]
    tot = {"renamed": 0, "demoted": 0, "toc": 0}
    files = 0
    for dp, dn, fn in os.walk(ROOT):
        if ".git" in dp or "node_modules" in dp:
            continue
        rel = os.path.relpath(dp, ROOT).split(os.sep)[0]
        if rel in ("tools",):
            continue
        for f in sorted(fn):
            if not f.endswith(".html"):
                continue
            p = os.path.join(dp, f)
            s = open(p, encoding="utf-8", errors="replace").read()
            new, st = process(s, os.path.relpath(p, ROOT), site, cfg)
            if new != s:
                files += 1
                for k in tot:
                    tot[k] += st[k]
                if not dry:
                    open(p, "w", encoding="utf-8").write(new)
    print(("DRY " if dry else "") + "[%s] 改动 %d 文件 | 标题差异化 %d | 转非标题 %d | 加TOC %d"
          % (site, files, tot["renamed"], tot["demoted"], tot["toc"]))


if __name__ == "__main__":
    main()

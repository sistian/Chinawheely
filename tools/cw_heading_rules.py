#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标题层级规范审计：跳级(H2→H4)、缺 H3、H1 位置、标题是否为空/过短/过长"""
import os, re, glob, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "*.html")))

THEME = re.compile(r"-(best-time|day-trips|photo-spots|food-shopping|tea-culture|airport-transfer-to-[a-z-]+)\.html$")

def headings(html):
    out = []
    for m in re.finditer(r"<(h[1-6])\b([^>]*)>([\s\S]{0,400}?)</\1\s*>", html, re.I):
        tag = m.group(1).lower()
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(3))).strip()
        out.append((tag, txt, m.start()))
    return out

stats = collections.Counter()
skip_h3 = []
empty_h = []
toolong = []
short_h = []
h1_out_main = []
multi_h1 = []

for f in FILES:
    h = open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read()
    m = re.search(r"<main[\s>][\s\S]*?</main>", h, re.I)
    main_span = (m.start(), m.end()) if m else None
    hs = headings(h)
    lv = [int(t[0][1]) for t in hs]
    for i, (tag, txt, pos) in enumerate(hs):
        if not txt:
            empty_h.append((f, tag)); stats["empty"] += 1
        if len(txt) > 110:
            toolong.append((f, tag, txt)); stats["toolong"] += 1
        if 0 < len(txt) < 8 and tag != "h1":
            short_h.append((f, tag, txt)); stats["short"] += 1
    if lv.count(1) > 1:
        multi_h1.append((f, lv.count(1)))
    if main_span and not any(t[0] == "h1" and main_span[0] <= t[2] <= main_span[1] for t in hs):
        h1_out_main.append(f)
    # 跳级检测：H2 之后直接 H4（跳过 H3）
    for i in range(len(hs) - 1):
        a, b = int(hs[i][0][1]), int(hs[i + 1][0][1])
        if a == 2 and b == 4:
            skip_h3.append((f, hs[i + 1][1][:46]))
            break
    if 2 in lv and 3 not in lv:
        stats["no_h3_at_all"] += 1

print("=" * 74)
print("【1】标题层级规范")
print("=" * 74)
print(f"   站点页面总数            : {len(FILES)}")
print(f"   H1 在 main 外           : {len(h1_out_main)}")
print(f"   多个 H1                 : {len(multi_h1)}")
print(f"   H2→H4 跳级(跳过 H3)      : {len(skip_h3)}")
print(f"   全文无 H3 的页           : {stats['no_h3_at_all']}")
print(f"   空标题                  : {stats['empty']}")
print(f"   标题过长 >110 字         : {stats['toolong']}")
print(f"   标题过短 <8 字           : {stats['short']}")

print("\n   跳级页（前 25）:")
for f, t in skip_h3[:25]:
    print(f"      {f:40s} H4: {t}")

print("\n   无 H3 的页（前 30）:")
cnt = 0
for f in FILES:
    h = open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read()
    m = re.search(r"<main[\s>][\s\S]*?</main>", h, re.I)
    scope = m.group(0) if m else h
    if re.search(r"<h2[\s>]", scope, re.I) and not re.search(r"<h3[\s>]", scope, re.I):
        print(f"      {f}")
        cnt += 1
        if cnt >= 30:
            break
print(f"      … 共 {stats['no_h3_at_all']} 页")

print("\n" + "=" * 74)
print("【2】标题过长（Google 会在 SERP 里截断）")
print("=" * 74)
for f, tag, t in toolong[:15]:
    print(f"   {f:30s} <{tag}> {t[:120]}")

print("\n" + "=" * 74)
print("【3】主题页 vs 城市页 的 H3 覆盖")
print("=" * 74)
tp = [f for f in FILES if THEME.search(f)]
cp = [f for f in FILES if not THEME.search(f)]
for nm, sel in (("主题页", tp), ("城市页", cp)):
    no3 = 0
    for f in sel:
        h = open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read()
        m = re.search(r"<main[\s>][\s\S]*?</main>", h, re.I)
        scope = m.group(0) if m else h
        if re.search(r"<h2[\s>]", scope, re.I) and not re.search(r"<h3[\s>]", scope, re.I):
            no3 += 1
    print(f"   {nm}: {len(sel)} 页，其中「有 H2 但无 H3」= {no3} 页")

json.dump({"skip_h3": skip_h3, "h1_out_main": h1_out_main, "toolong": toolong,
           "empty": empty_h, "short": short_h}, open("/tmp/heading_rules.json", "w"), ensure_ascii=False)
print("\n→ /tmp/heading_rules.json")

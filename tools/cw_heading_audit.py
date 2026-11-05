#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""城市页体检：标题层级(H1/H2/H3) + 正文深度 + 薄弱点定位"""
import os, re, glob, json
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CITY = set()
for p in glob.glob(os.path.join(ROOT, "*.html")):
    b = os.path.basename(p)
    if b in ("index.html",):
        continue
    CITY.add(b)

# 主题页/功能页单独归类
THEME = re.compile(r"^(beijing|shanghai|guangzhou|shenzhen)-.*\.html$")

def text_of(html):
    h = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    h = re.sub(r"<style[\s\S]*?</style>", " ", h, flags=re.I)
    h = re.sub(r"<!--[\s\S]*?-->", " ", h)
    h = re.sub(r"<[^>]+>", " ", h)
    h = re.sub(r"&nbsp;", " ", h)
    h = re.sub(r"&amp;", "&", h)
    h = re.sub(r"\s+", " ", h)
    return h.strip()

rows = []
for b in sorted(CITY):
    p = os.path.join(ROOT, b)
    if not os.path.isfile(p):
        continue
    html = open(p, encoding="utf-8", errors="ignore").read()
    body = html.split("</main>")[0] if "</main>" in html else html
    # 只看 main 内的标题
    m = re.search(r"<main[\s>][\s\S]*?</main>", html, re.I)
    scope = m.group(0) if m else body
    h1 = re.findall(r"<h1[\s>]", scope, re.I)
    h2 = re.findall(r"<h2[\s>]", scope, re.I)
    h3 = re.findall(r"<h3[\s>]", scope, re.I)
    h4 = re.findall(r"<h4[\s>]", scope, re.I)
    # 全页（含 footer）标题数
    ah1 = len(re.findall(r"<h1[\s>]", html, re.I))
    ah2 = len(re.findall(r"<h2[\s>]", html, re.I))
    ah3 = len(re.findall(r"<h3[\s>]", html, re.I))
    txt = text_of(scope)
    words = len(txt.split())
    rows.append({
        "file": b, "h1": len(h1), "h2": len(h2), "h3": len(h3), "h4": len(h4),
        "ah1": ah1, "ah2": ah2, "ah3": ah3, "words": words,
        "bytes": len(html),
        "theme": bool(THEME.match(b)),
    })

def bucket(rows, key, fn):
    c = Counter(fn(r) for r in rows)
    return c

print("=" * 72)
print(f"城市页总数（排除 index.html）: {len(rows)}")
print("=" * 72)

# ── H1 ─────────────────────────────────────────────
print("\n【A】一级标题 H1")
h1n = bucket(rows, None, lambda r: r["h1"])
for k in sorted(h1n):
    print(f"   main 内 H1 = {k} 个 : {h1n[k]} 页")
bad_h1 = [r for r in rows if r["h1"] != 1]
print(f"   ⚠ H1≠1 的页: {len(bad_h1)}")
for r in bad_h1[:15]:
    print(f"      {r['file']}: main H1={r['h1']}, 全页 H1={r['ah1']}")

# ── H2 ─────────────────────────────────────────────
print("\n【B】二级标题 H2")
h2n = bucket(rows, None, lambda r: r["h2"])
for k in sorted(h2n):
    print(f"   main 内 H2 = {k} 个 : {h2n[k]} 页")
no_h2 = [r for r in rows if r["h2"] < 2]
print(f"   ⚠ H2 < 2 的页: {len(no_h2)}")
for r in sorted(no_h2, key=lambda x: x["h2"])[:15]:
    print(f"      {r['file']}: H2={r['h2']} 词数={r['words']}")

# ── H3 ─────────────────────────────────────────────
print("\n【C】三级标题 H3")
h3n = bucket(rows, None, lambda r: r["h3"])
for k in sorted(h3n):
    print(f"   main 内 H3 = {k} 个 : {h3n[k]} 页")
no_h3 = [r for r in rows if r["h3"] < 2]
print(f"   ⚠ H3 < 2 的页: {len(no_h3)}")
for r in sorted(no_h3, key=lambda x: x["h3"])[:15]:
    print(f"      {r['file']}: H3={r['h3']} 词数={r['words']}")

# ── 正文深度 ───────────────────────────────────────
print("\n【D】正文词数分布")
buckets = [("严重不足 (<300)", lambda w: w < 300), ("偏薄 (300-600)", lambda w: 300 <= w < 600),
           ("及格 (600-1000)", lambda w: 600 <= w < 1000), ("良好 (1000-1500)", lambda w: 1000 <= w < 1500),
           ("充足 (1500+)", lambda w: w >= 1500)]
for label, fn in buckets:
    sel = [r for r in rows if fn(r["words"])]
    print(f"   {label:22s}: {len(sel)} 页")
thin = sorted([r for r in rows if r["words"] < 600], key=lambda x: x["words"])
print(f"\n   最薄的 20 页:")
for r in thin[:20]:
    print(f"      {r['file']:32s} 词数={r['words']:5d} H1={r['h1']} H2={r['h2']} H3={r['h3']} 主题页={r['theme']}")

# ── 主题页 vs 城市页 ───────────────────────────────
print("\n【E】主题页 vs 城市页")
tp = [r for r in rows if r["theme"]]
cp = [r for r in rows if not r["theme"]]
for nm, sel in (("主题页", tp), ("城市页", cp)):
    if not sel: continue
    print(f"   {nm}: {len(sel)} 页 | 平均词数 {sum(x['words'] for x in sel)//len(sel)} | "
          f"平均 H2 {sum(x['h2'] for x in sel)/len(sel):.1f} | 平均 H3 {sum(x['h3'] for x in sel)/len(sel):.1f} | "
          f"H2<2 的 {sum(1 for x in sel if x['h2']<2)} | H3<2 的 {sum(1 for x in sel if x['h3']<2)}")

json.dump(rows, open("/tmp/heading_audit.json", "w"), ensure_ascii=False)
print(f"\n→ /tmp/heading_audit.json")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""省份一致性(修正变量名) + 近似重复内容检测 + zhouzhuang/suzhou 重复核查"""
import os, re, glob, json, importlib.util, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = "/Users/w/.openclaw/workspace/city_facts"

spec = importlib.util.spec_from_file_location("cpm", os.path.join(ROOT, "tools", "city_province_map.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
PROV = m.CITY_PROV
print("=" * 72)
print(f"【1】省份一致性（权威表 {len(PROV)} 条）")
print("=" * 72)

fact_files = {os.path.basename(p)[:-5]: p for p in glob.glob(os.path.join(FACTS, "*.json"))}
bad = []
for slug, p in fact_files.items():
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    got = d.get("province_en") or d.get("province")
    exp = PROV.get(slug)
    if got and exp and str(got).strip().lower() != str(exp).strip().lower():
        bad.append((slug, exp, got))
if not bad:
    print("   ✅ 全部 city_facts 省份与权威表一致")
for s, e, g in bad:
    print(f"   🔴 {s:26s} 权威={e}  facts={g}")

# 页面里写的省份 vs 权威表
print("\n   页面正文省份 vs 权威表：")
bad2 = []
for slug, exp in PROV.items():
    fp = os.path.join(ROOT, slug + ".html")
    if not os.path.isfile(fp):
        continue
    h = open(fp, encoding="utf-8", errors="ignore").read()
    txt = re.sub(r"<[^>]+>", " ", h)
    m2 = re.search(r"Local Province\s*:?\s*([A-Z][A-Za-z ]{2,20})", txt)
    if m2 and m2.group(1).strip().lower() != str(exp).strip().lower():
        bad2.append((slug, exp, m2.group(1).strip()))
if not bad2:
    print("   ✅ 页面内省份标注全部一致")
for s, e, g in bad2[:20]:
    print(f"   🔴 {s:26s} 权威={e}  页面={g}")

print("\n" + "=" * 72)
print("【2】近似重复内容（5-gram Jaccard，阈值 0.45）")
print("=" * 72)

def grams(html, n=5):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<!--[\s\S]*?-->", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"[^A-Za-z0-9 ]+", " ", t).lower()
    w = t.split()
    return set(" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1)))

files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "*.html")))
CITY = [f for f in files if f not in ("index.html",) and not f.endswith(("-best-time.html", "-day-trips.html",
          "-photo-spots.html", "-food-shopping.html", "-tea-culture.html"))]
G = {f: grams(open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read()) for f in CITY}
G = {k: v for k, v in G.items() if len(v) > 30}
print(f"   参与比对: {len(G)} 个城市页")
pairs = []
items = list(G.items())
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        a, b = items[i], items[j]
        inter = len(a[1] & b[1])
        if not inter:
            continue
        jac = inter / len(a[1] | b[1])
        if jac >= 0.45:
            pairs.append((jac, a[0], b[0]))
pairs.sort(reverse=True)
if not pairs:
    print("   ✅ 无近似重复页对（阈值 0.45）")
for jac, a, b in pairs[:20]:
    print(f"   🔴 {jac:.3f}  {a}  ≈  {b}")

print("\n" + "=" * 72)
print("【3】zhouzhuang.html vs suzhou.html 重复核查")
print("=" * 72)
for a, b in [("zhouzhuang.html", "suzhou.html"), ("taizhou_js.html", "taizhou.html")]:
    if not os.path.isfile(os.path.join(ROOT, a)):
        print(f"   {a}: 文件不存在"); continue
    ga, gb = G.get(a), G.get(b)
    if ga and gb:
        jac = len(ga & gb) / len(ga | gb)
        print(f"   {a} vs {b}: 5-gram Jaccard = {jac:.3f}")
    ha = re.sub(r"<[^>]+>", " ", open(os.path.join(ROOT, a), encoding="utf-8").read())
    print(f"   {a} 词数={len(ha.split())}")

print("\n" + "=" * 72)
print("【4】主题页与其母城页的重复度")
print("=" * 72)
TH = [f for f in files if f.endswith(("-best-time.html", "-day-trips.html", "-photo-spots.html",
                                       "-food-shopping.html", "-tea-culture.html"))]
print(f"   主题页 {len(TH)} 个")
worst = []
for t in TH:
    city = t.rsplit("-", 1)[0] + ".html"
    if city not in G or t not in G:
        continue
    gt = grams(open(os.path.join(ROOT, t), encoding="utf-8", errors="ignore").read())
    if len(gt) < 20:
        continue
    jac = len(gt & G[city]) / len(gt | G[city])
    worst.append((jac, t, city))
worst.sort(reverse=True)
hi = [w for w in worst if w[0] >= 0.30]
print(f"   与母城页相似度 ≥0.30 的: {len(hi)}")
for jac, t, c in hi[:15]:
    print(f"   ⚠ {jac:.3f}  {t}  ≈  {c}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站段落模板化分析 v2：把 H2 里的【真实城市名/省份名】替换成占位符后再分组"""
import os, re, glob, json, collections, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = "/Users/w/.openclaw/workspace/city_facts"
FILES = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "*.html")))

# 城市显示名（来自 city_facts，其次 H1）
names = {}
for p in glob.glob(os.path.join(FACTS, "*.json")):
    slug = os.path.basename(p)[:-5]
    try:
        d = json.load(open(p, encoding="utf-8"))
        names[slug] = (d.get("city_en") or slug.title(), d.get("province_en") or "")
    except Exception:
        pass

def sections(path):
    h = open(path, encoding="utf-8", errors="ignore").read()
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S | re.I)
    m = re.search(r"<main[\s>][\s\S]*?</main>", h, re.I)
    h = m.group(0) if m else h
    parts = re.split(r"(<h2[^>]*>.*?</h2>)", h, flags=re.S | re.I)
    out, cur, buf = [], "PRE", []
    for p in parts:
        if re.match(r"<h2", p, re.I):
            if buf:
                out.append((cur, " ".join(buf)))
            cur = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", p)).strip()
            buf = []
        else:
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", p)).strip()
            if t:
                buf.append(t)
    if buf:
        out.append((cur, " ".join(buf)))
    return out

def ngrams(s, n=6):
    w = re.sub(r"[^a-z0-9 ]+", " ", s.lower()).split()
    return set(" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1)))

CITY = [f for f in FILES if not re.search(
    r"-(best-time|day-trips|photo-spots|food-shopping|tea-culture|airport-transfer-to-[a-z-]+)\.html$", f)]
print(f"分析城市页 {len(CITY)} 个\n")

bypat = collections.defaultdict(list)
for f in CITY:
    slug = f[:-5]
    cn, prov = names.get(slug, (slug.replace("_", " ").title(), ""))
    for h, t in sections(os.path.join(ROOT, f)):
        pat = h
        for token in (cn, prov):
            if token and len(token) > 2:
                pat = re.sub(re.escape(token), "{C}", pat, flags=re.I)
        pat = re.sub(r"'s\b", "'s", pat)
        pat = re.sub(r"\s+", " ", pat).strip().lower()
        bypat[pat].append((f, t))

print("=" * 80)
print("【段落模板化排行】")
print("=" * 80)
print(f"{'页数':>4} {'同质度':>7} {'均词数':>7}  模板")
rows = []
for pat, items in bypat.items():
    if len(items) < 3:
        continue
    gs = [ngrams(t) for _, t in items]
    gs = [g for g in gs if len(g) >= 8]
    if len(gs) < 3:
        continue
    random.seed(7)
    pairs = []
    for _ in range(min(500, len(gs) * 4)):
        i, j = random.sample(range(len(gs)), 2)
        pairs.append(len(gs[i] & gs[j]) / max(1, len(gs[i] | gs[j])))
    avg = sum(pairs) / len(pairs)
    avgw = sum(len(t.split()) for _, t in items) // len(items)
    rows.append((avg, len(items), avgw, pat))
rows.sort(reverse=True)
for avg, n, w, pat in rows[:30]:
    print(f"{n:>4} {avg:>7.2f} {w:>7}  {pat[:56]:58s}{'█'*int(avg*26)}")

print("\n" + "=" * 80)
print("【同质度分层】")
print("=" * 80)
tot_w = sum(w * n for _, n, w, _ in rows)
for lo, hi, lab in [(0.9, 1.01, "近乎全同 ≥0.90"), (0.6, 0.9, "高度模板 0.60-0.90"),
                    (0.3, 0.6, "中度模板 0.30-0.60"), (0, 0.3, "基本独有 <0.30")]:
    sel = [r for r in rows if lo <= r[0] < hi]
    w = sum(x[1] * x[2] for x in sel)
    print(f"   {lab:22s}: {len(sel):>3} 类模板, 覆盖 {w:>6} 词 = {w*100//max(1,tot_w):>3}%")
print(f"\n   模板化(≥0.6) 合计覆盖正文 {sum(x[1]*x[2] for x in rows if x[0]>=0.6)*100//max(1,tot_w)}%")

json.dump([{"sim": round(a, 3), "pages": n, "words": w, "pattern": p} for a, n, w, p in rows],
          open("/tmp/template_patterns.json", "w"), ensure_ascii=False, indent=1)
print("→ /tmp/template_patterns.json")

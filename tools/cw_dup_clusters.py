#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重复聚类分析：把近似重复的页面聚成簇，评估重复率"""
import os, re, glob, json, collections, itertools

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def grams(html, n=5):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<!--[\s\S]*?-->", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"[^A-Za-z0-9 ]+", " ", t).lower()
    w = t.split()
    return set(" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1)))

files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "*.html")))
G = {}
for f in files:
    s = grams(open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read())
    if len(s) > 30:
        G[f] = s

# 用倒排索引加速候选对
inv = collections.defaultdict(set)
for f, s in G.items():
    for g in list(s)[:400]:
        inv[g].add(f)

cands = collections.Counter()
for g, fs in inv.items():
    if 2 <= len(fs) <= 40:
        for a, b in itertools.combinations(sorted(fs), 2):
            cands[(a, b)] += 1

TH = 0.45
edges = []
for (a, b), c in cands.items():
    inter = len(G[a] & G[b])
    if not inter:
        continue
    jac = inter / len(G[a] | G[b])
    if jac >= TH:
        edges.append((jac, a, b))
edges.sort(reverse=True)

parent = {f: f for f in G}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[rb] = ra

for _, a, b in edges:
    union(a, b)

clusters = collections.defaultdict(list)
for f in G:
    clusters[find(f)].append(f)
multi = {k: v for k, v in clusters.items() if len(v) > 1}
multi = dict(sorted(multi.items(), key=lambda kv: -len(kv[1])))

print("=" * 72)
print(f"【重复聚类】阈值 {TH} | 参与页 {len(G)} | 重复边 {len(edges)}")
print("=" * 72)
print(f"   涉及重复的簇 = {len(multi)} 个")
dup_pages = sum(len(v) for v in multi.values())
print(f"   处于重复簇中的页面 = {dup_pages} 页（占 {dup_pages*100//max(1,len(G))}%）")
print(f"   独立无重复页 = {len(G) - dup_pages} 页\n")

print("【按类型拆分重复簇】")
TYPES = {
    "机场接送主题页 airport-transfer-to": lambda f: "-airport-transfer-to-" in f,
    "主题页 tea/best-time/day-trips/photo/food": lambda f: f.endswith(("-tea-culture.html", "-best-time.html",
        "-day-trips.html", "-photo-spots.html", "-food-shopping.html")),
    "普通城市页": lambda f: True,
}
for name, fn in TYPES.items():
    sel = [(j, a, b) for j, a, b in edges if fn(a) and fn(b)]
    print(f"   {name:46s}: {len(sel)} 对")

print("\n【最大的 12 个重复簇】")
for k, v in list(multi.items())[:12]:
    v = sorted(v)
    print(f"   ▸ {len(v)} 页: {', '.join(v[:6])}{' …' if len(v) > 6 else ''}")
    worst = max((e for e in edges if e[1] in v and e[2] in v), default=None)
    if worst:
        print(f"       最相似 {worst[0]:.3f}  ({worst[1]} ≈ {worst[2]})")

print("\n【完全被同质化的小城页（与 >=6 个其它页相似）】")
deg = collections.Counter()
for _, a, b in edges:
    deg[a] += 1; deg[b] += 1
hot = [(d, f) for f, d in deg.items() if d >= 6]
hot.sort(reverse=True)
print(f"   与 >=6 个页面高度相似的页 = {len(hot)}")
for d, f in hot[:25]:
    print(f"      {f:34s} 与 {d} 个页面相似")

json.dump({"dup_pages": dup_pages, "clusters": {str(k): v for k, v in list(multi.items())[:50]},
           "hot": hot[:40]}, open("/tmp/dup_clusters.json", "w"), ensure_ascii=False)
print("\n→ /tmp/dup_clusters.json")

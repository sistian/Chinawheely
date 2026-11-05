#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收录深度诊断：sitemap 里的页 HTTP 状态 / 主题页收录情况 / 孤儿页 / 页面体积"""
import os, re, glob, json, urllib.request, urllib.error, collections, concurrent.futures

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.chinawheely.com"

r = urllib.request.urlopen(BASE + "/sitemap.xml", timeout=30)
sm = r.read().decode()
urls = re.findall(r"<loc>([^<]+)</loc>", sm)

print("=" * 72)
print("【1】sitemap URL 抽样 HTTP 状态（每 12 个抽 1 个）")
print("=" * 72)
sample = urls[::12]
bad = []

def head(u):
    try:
        req = urllib.request.Request(u, method="GET", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as rr:
            return u, rr.status, len(rr.read())
    except urllib.error.HTTPError as e:
        return u, e.code, 0
    except Exception as e:
        return u, 0, str(e)[:40]

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    for u, st, n in ex.map(head, sample):
        if st != 200:
            bad.append((u, st, n)); print(f"   ❌ {st} {u.replace(BASE,'')}")
print(f"   抽样 {len(sample)} 个，非 200 的 {len(bad)} 个")

print("\n" + "=" * 72)
print("【2】主题页在 sitemap / robots / 索引信号中的状态")
print("=" * 72)
files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "*.html")))
THEME_KINDS = ["tea-culture", "best-time", "day-trips", "photo-spots", "food-shopping"]
theme = [f for f in files if any(f.endswith("-" + k + ".html") for k in THEME_KINDS)]
print(f"   主题页总数 = {len(theme)}")
in_sm = [f for f in theme if f"{BASE}/{f}" in urls]
print(f"   在 sitemap 里 = {len(in_sm)} / {len(theme)}")
notin = [f for f in theme if f"{BASE}/{f}" not in urls]
print(f"   不在 sitemap 的主题页（前 30）:")
for f in notin[:30]:
    print("      ", f)
noindex_theme = []
for f in theme:
    h = open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read()
    head_ = h.split("</head>")[0] if "</head>" in h else h[:20000]
    if re.search(r'name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', head_, re.I):
        noindex_theme.append(f)
print(f"\n   带 noindex 的主题页 = {len(noindex_theme)}")
for f in noindex_theme[:20]:
    print("      ", f)

print("\n" + "=" * 72)
print("【3】孤儿页（sitemap 有但站内无入链）")
print("=" * 72)
link_count = collections.Counter()
for f in files:
    h = open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read()
    for m in re.findall(r'href=["\']([^"\'#?]+)', h):
        tgt = os.path.basename(m.strip("/"))
        if tgt.endswith(".html"):
            link_count[tgt] += 1
orphans = [f for f in files if f not in link_count and f not in ("index.html",)]
print(f"   零入链页 = {len(orphans)}")
for f in orphans[:30]:
    tag = " [sitemap外]" if f"{BASE}/{f}" not in urls else ""
    print(f"      {f}{tag}")

print("\n" + "=" * 72)
print("【4】页面体积（HTML 字节，大页影响抓取与速度）")
print("=" * 72)
sizes = []
for f in files:
    sizes.append((os.path.getsize(os.path.join(ROOT, f)), f))
sizes.sort(reverse=True)
tot = sum(s for s, _ in sizes)
print(f"   合计 {tot/1024/1024:.1f} MB，平均 {tot//len(sizes)/1024} KB")
print("   最大 15 页:")
for s, f in sizes[:15]:
    print(f"      {s/1024:8.0f} KB  {f}")
buckets = [(0, 80, "<80KB"), (80, 150, "80-150KB"), (150, 300, "150-300KB"), (300, 10**9, ">300KB")]
for lo, hi, lab in buckets:
    n = sum(1 for s, _ in sizes if lo <= s / 1024 < hi)
    print(f"   {lab:12s}: {n} 页")

print("\n" + "=" * 72)
print("【5】图片资源体积（首页 + 代表城市页）")
print("=" * 72)
for f in ["index.html", "beijing.html", "shanghai.html"]:
    p = os.path.join(ROOT, f)
    if not os.path.isfile(p):
        continue
    h = open(p, encoding="utf-8", errors="ignore").read()
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)', h)
    tot_i = 0
    for im in imgs:
        ip = os.path.join(ROOT, im.lstrip("./"))
        if os.path.isfile(ip):
            tot_i += os.path.getsize(ip)
    print(f"   {f}: {len(imgs)} 张图，合计 {tot_i/1024:.0f} KB")

json.dump({"theme_total": len(theme), "theme_in_sitemap": len(in_sm),
           "theme_noindex": noindex_theme, "orphans": orphans,
           "sample_bad": bad}, open("/tmp/deep_index.json", "w"), ensure_ascii=False)
print("\n→ /tmp/deep_index.json")

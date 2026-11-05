#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收录诊断：robots / sitemap / noindex / canonical / 状态码 / 内链 / 孤儿页"""
import os, re, glob, json, urllib.request, urllib.error, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.chinawheely.com"

print("=" * 72)
print("【1】robots.txt")
print("=" * 72)
try:
    r = urllib.request.urlopen(BASE + "/robots.txt", timeout=30)
    rob = r.read().decode()
    print(f"http={r.status}")
    for ln in rob.strip().splitlines():
        print("   ", ln)
except Exception as e:
    print("❌ 读取失败:", e)
    rob = ""

print("\n" + "=" * 72)
print("【2】sitemap.xml")
print("=" * 72)
sm = None
for cand in ["sitemap.xml", "sitemap_index.xml"]:
    try:
        r = urllib.request.urlopen(BASE + "/" + cand, timeout=30)
        s = r.read().decode()
        print(f"{cand}: http={r.status}  {len(s)} 字节")
        if "<sitemapindex" in s:
            subs = re.findall(r"<loc>([^<]+)</loc>", s)
            print(f"   sitemap index, {len(subs)} 个子 sitemap:")
            for u in subs[:10]:
                print("     ", u)
            for u in subs:
                try:
                    rr = urllib.request.urlopen(u, timeout=30)
                    ss = rr.read().decode()
                    n = len(re.findall(r"<loc>", ss))
                    print(f"     → {u} : {n} 条")
                    sm = sm or ss
                    if sm is not ss:
                        sm += ss
                except Exception as e:
                    print(f"     → {u} 读取失败 {e}")
        else:
            sm = s
    except Exception as e:
        print(f"{cand}: ❌ {e}")

urls = set(re.findall(r"<loc>([^<]+)</loc>", sm or ""))
print(f"\n   sitemap 总 URL 数 = {len(urls)}")
files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "*.html")))
print(f"   站点实际 html 文件 = {len(files)}")

# 本地页面 → 期望 URL
expected = set()
for f in files:
    expected.add(f"{BASE}/{f}")

missing_from_sitemap = sorted(expected - urls)
extra_in_sitemap = sorted(urls - expected)
print(f"\n   ⚠ 在站内但不在 sitemap: {len(missing_from_sitemap)}")
for u in missing_from_sitemap[:40]:
    print("      ", u.replace(BASE, ""))
print(f"   ⚠ 在 sitemap 但站内文件不存在: {len(extra_in_sitemap)}")
for u in extra_in_sitemap[:20]:
    print("      ", u.replace(BASE, ""))

print("\n" + "=" * 72)
print("【3】页面级索引信号（本地扫描）")
print("=" * 72)
noindex, canonical_bad, robots_bad, canon_missing, og_bad = [], [], [], [], []
hreflang_pages = 0
for f in files:
    p = os.path.join(ROOT, f)
    h = open(p, encoding="utf-8", errors="ignore").read()
    head = h.split("</head>")[0] if "</head>" in h else h[:20000]
    mr = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']+)', head, re.I)
    if mr:
        c = mr.group(1).lower()
        if "noindex" in c:
            noindex.append((f, c))
    # canonical
    mc = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', head, re.I)
    if not mc:
        canon_missing.append(f)
    else:
        cu = mc.group(1)
        if not cu.rstrip("/").endswith(f.replace(".html", "")) and not cu.rstrip("/").endswith(f):
            canonical_bad.append((f, cu))
    mo = re.search(r'<meta[^>]+property=["\']og:url["\'][^>]*content=["\']([^"\']+)', head, re.I)
    if mc and mo and mo.group(1).rstrip("/") != mc.group(1).rstrip("/"):
        og_bad.append((f, mc.group(1), mo.group(1)))
    if 'hreflang=' in head:
        hreflang_pages += 1

print(f"   带 noindex 的页: {len(noindex)}")
for f, c in noindex[:30]:
    print(f"      {f:36s} {c}")
print(f"\n   缺 canonical 的页: {len(canon_missing)}")
for f in canon_missing[:20]:
    print("      ", f)
print(f"\n   canonical 非自指的页: {len(canonical_bad)}")
for f, u in canonical_bad[:25]:
    print(f"      {f:32s} → {u.replace(BASE,'')}")
print(f"\n   canonical ≠ og:url 的页: {len(og_bad)}")
for f, a, b in og_bad[:15]:
    print(f"      {f:32s} {a.replace(BASE,'')}  ≠  {b.replace(BASE,'')}")
print(f"\n   含 hreflang 的页: {hreflang_pages}")

json.dump({"sitemap": len(urls), "files": len(files),
           "missing_sitemap": [u.replace(BASE, "") for u in missing_from_sitemap],
           "noindex": noindex, "canon_missing": canon_missing,
           "canon_bad": canonical_bad, "og_bad": og_bad},
          open("/tmp/index_audit.json", "w"), ensure_ascii=False)
print("\n→ /tmp/index_audit.json")

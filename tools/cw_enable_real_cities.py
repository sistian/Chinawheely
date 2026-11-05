#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阶段 A（不依赖 DNS，立即生效于 GitHub Pages）：
1. 5 个「同名不同省」的真实城市页：取消 noindex → index,follow，canonical 自指
2. 加入 sitemap.xml
3. 站内指向桩页的内链改为直指最终目标
幂等：重复运行结果一致。
"""
import os, re, glob, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.chinawheely.com"

# ── 1. 恢复索引的 5 个真实城市页 ─────────────────────────────
REAL = {
    "taizhou_js.html": "Taizhou, Jiangsu",
    "yichun_hlj.html": "Yichun, Heilongjiang",
    "suzhou_ah.html": "Suzhou, Anhui",
    "fuzhou_jx.html": "Fuzhou, Jiangxi",
    "yulin_sx.html": "Yulin, Shaanxi",
}
# ── 2. 桩页 → 最终目标（用于改内链）────────────────────────
STUB_TO = {
    "taizhou_zj.html": "taizhou.html",
    "yichun_jx.html": "yichun.html",
    "yichun-heilongjiang.html": "yichun_hlj.html",
    "suzhou-jiangsu.html": "suzhou.html",
    "beijing_detailed.html": "beijing.html",
    "erdos.html": "eerduosi.html",
    "hulunbeier.html": "eerduosi.html",
    "jdz.html": "jingdezhen.html",
    "jinzhou_ln.html": "jinzhou.html",
    "jl.html": "jilin.html",
    "juncheng.html": "yuncheng.html",
    "kelamayi.html": "karamay.html",
    "wulumuqi.html": "urumqi.html",
    "yan_an.html": "yanan.html",
}

changed = {"robots": [], "canonical": [], "sitemap": [], "inlinks": []}

# ── 1+2: 取消 noindex + canonical 自指 ──────────────────────
for f, city in REAL.items():
    p = os.path.join(ROOT, f)
    h = open(p, encoding="utf-8").read()
    orig = h
    # robots: noindex, follow → index, follow
    h2, n = re.subn(
        r'(<meta[^>]+name=["\']robots["\'][^>]*content=["\'])\s*noindex\s*,\s*follow\s*(["\'])',
        r'\1index, follow\2', h, flags=re.I)
    if n:
        changed["robots"].append(f)
        h = h2
    # canonical 自指
    h3, n = re.subn(
        r'(<link[^>]+rel=["\']canonical["\'][^>]*href=["\'])[^"\']*(["\'])',
        lambda m: m.group(1) + f"/{f}" + m.group(2), h, count=1, flags=re.I)
    if n:
        changed["canonical"].append(f)
        h = h3
    if h != orig:
        open(p, "w", encoding="utf-8").write(h)

# ── 3: sitemap 加入这 5 页 ──────────────────────────────────
sp = os.path.join(ROOT, "sitemap.xml")
s = open(sp, encoding="utf-8").read()
existing = set(re.findall(r"<loc>([^<]+)</loc>", s))
added = []
for f in REAL:
    u = f"{BASE}/{f}"
    if u in existing:
        continue
    m = re.search(r"<url>.*?</url>", s, re.S)
    if not m:
        continue
    block = (f"  <url>\n    <loc>{u}</loc>\n"
             f"    <lastmod>{__import__('datetime').date.today().isoformat()}</lastmod>\n"
             f"    <changefreq>weekly</changefreq>\n"
             f"    <priority>0.7</priority>\n  </url>\n")
    s = s[:m.start()] + block + s[m.start():]
    added.append(f)
if added:
    open(sp, "w", encoding="utf-8").write(s)
    changed["sitemap"] = added

# ── 4: 站内内链 桩页 → 最终目标 ─────────────────────────────
for src in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
    sf = os.path.basename(src)
    if sf in STUB_TO:
        continue          # 桩页自身的文件保留
    h = open(src, encoding="utf-8").read()
    orig = h
    for stub, tgt in STUB_TO.items():
        # 只改 <a href> 链接，不碰 canonical / og:url
        h = re.sub(rf'(<a\b[^>]*?href=["\'])/{re.escape(stub)}(["\'])',
                   rf'\1/{tgt}\2', h)
        h = re.sub(rf'(<a\b[^>]*?href=["\']){re.escape(stub)}(["\'])',
                   rf'\1/{tgt}\2', h)
    if h != orig:
        open(src, "w", encoding="utf-8").write(h)
        changed["inlinks"].append(sf)

print("=" * 70)
print("阶段 A 执行结果")
print("=" * 70)
print(f"  取消 noindex        : {len(changed['robots'])} 页  {changed['robots']}")
print(f"  canonical 改为自指   : {len(changed['canonical'])} 页  {changed['canonical']}")
print(f"  加入 sitemap        : {len(changed['sitemap'])} 页  {changed['sitemap']}")
print(f"  内链改指最终目标     : {len(changed['inlinks'])} 页  {changed['inlinks'][:20]}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 301 重定向表：识别所有「This page has moved」桩页 → 权威目标，
校验：目标存在 / 目标可索引 / 非自我 / 词数对比 / 站内入链情况"""
import os, re, glob, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "*.html")))

def head_of(f):
    h = open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read()
    return h, (h.split("</head>")[0] if "</head>" in h else h[:20000])

def meta(head, name):
    m = re.search(rf'<meta[^>]+name=["\']{name}["\'][^>]*content=["\']([^"\']+)', head, re.I)
    return m.group(1) if m else ""

def link(head, rel):
    m = re.search(rf'<link[^>]+rel=["\']{rel}["\'][^>]*href=["\']([^"\']+)', head, re.I)
    return m.group(1) if m else ""

print("=" * 78)
print("【A】所有「This page has moved」桩页")
print("=" * 78)
stubs = []
for f in FILES:
    h, head = head_of(f)
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
    if re.search(r"This page has moved", txt, re.I):
        words = len(txt.split())
        stubs.append((f, words, meta(head, "robots"), link(head, "canonical"),
                      link(head, "canonical").replace("https://www.chinawheely.com", "") if link(head, "canonical") else ""))
for f, w, r, c, cs in stubs:
    print(f"   {f:28s} 词数={w:4d} robots={r[:18]:20s} canonical={cs}")

# 站内入链统计
inlinks = collections.Counter()
for f in FILES:
    h, _ = head_of(f)
    for m in re.finditer(r'href=["\']([^"\'#?]+)', h):
        t = os.path.basename(m.group(1).strip("/"))
        if t.endswith(".html"):
            inlinks[t] += 1

print("\n" + "=" * 78)
print("【B】重定向映射（权威目标）")
print("=" * 78)
TARGET = {
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
ok = True
plan = []
for f, w, r, c, cs in stubs:
    tgt = TARGET.get(f)
    if not tgt:
        print(f"   ❌ {f:28s} 未定义目标！")
        ok = False
        continue
    if not os.path.isfile(os.path.join(ROOT, tgt)):
        print(f"   ❌ {f:28s} 目标 {tgt} 不存在")
        ok = False
        continue
    th, thead = head_of(tgt)
    trobots = meta(thead, "robots")
    tcanon = link(thead, "canonical").replace("https://www.chinawheely.com", "")
    twords = len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ",
        re.sub(r"<script.*?</script>|<style.*?</style>", " ", th, flags=re.S))).split())
    warn = []
    if "noindex" in trobots.lower():
        warn.append("⚠ 目标页自己 noindex")
    if tcanon.rstrip("/") not in ("/" + tgt, tgt):
        warn.append(f"⚠ 目标 canonical 非自指({tcanon})")
    if twords < 800:
        warn.append(f"⚠ 目标词数偏少({twords})")
    if inlinks[f]:
        warn.append(f"ℹ 有 {inlinks[f]} 处站内入链（301 会保留信号，但建议改成直链）")
    print(f"   {'✅' if not warn else 'ℹ'} {f:28s} → /{tgt:24s} 目标词数={twords:5d} robots={trobots[:16]:18s}"
          + ("  " + " ".join(warn) if warn else ""))
    plan.append({"from": f, "to": tgt, "inlinks": inlinks[f], "warnings": warn})

print("\n" + "=" * 78)
print("【C】无 noindex 的真实城市页（同名不同省，应恢复索引）")
print("=" * 78)
REAL = ["taizhou_js.html", "yichun_hlj.html", "suzhou_ah.html", "fuzhou_jx.html", "yulin_sx.html"]
for f in REAL:
    h, head = head_of(f)
    trobots = meta(head, "robots")
    tcanon = link(head, "canonical").replace("https://www.chinawheely.com", "")
    tw = len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ",
        re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S))).split())
    insm = f"https://www.chinawheely.com/{f}" in open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    print(f"   {f:22s} 词数={tw:5d} robots={trobots[:16]:18s} canonical={tcanon:22s} 在sitemap={insm}")

json.dump(plan, open("/tmp/redirect_plan.json", "w"), ensure_ascii=False, indent=1)
print("\n→ /tmp/redirect_plan.json")

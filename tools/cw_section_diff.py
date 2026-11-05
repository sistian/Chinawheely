#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 H2 分段，对比同簇两页各段落的重复率 —— 定位「哪一段被复制粘贴了」"""
import os, re, glob, collections, sys, difflib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def sections(path):
    h = open(path, encoding="utf-8", errors="ignore").read()
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S | re.I)
    m = re.search(r"<main[\s>][\s\S]*?</main>", h, re.I)
    h = m.group(0) if m else h
    # 按 H2 切段
    parts = re.split(r"(<h2[^>]*>.*?</h2>)", h, flags=re.S | re.I)
    out = []
    cur = "（前言）"
    buf = []
    for p in parts:
        if re.match(r"<h2", p, re.I):
            if buf:
                out.append((cur, " ".join(buf)))
            t = re.sub(r"<[^>]+>", " ", p)
            cur = re.sub(r"\s+", " ", t).strip()[:70]
            buf = []
        else:
            t = re.sub(r"<[^>]+>", " ", p)
            t = re.sub(r"\s+", " ", t).strip()
            if t:
                buf.append(t)
    if buf:
        out.append((cur, " ".join(buf)))
    return out

def ngrams(s, n=6):
    w = re.sub(r"[^a-z0-9 ]+", " ", s.lower()).split()
    return set(" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1)))

PAIRS = [("ankang.html", "anyang.html"), ("baise.html", "baishan.html"),
         ("xinyu.html", "xuwen.html"), ("haidong.html", "huaning.html"),
         ("rikaze.html", "ziyang.html")]
print("=" * 76)
print("【按 H2 段落对比：重复段 vs 独有段】")
print("=" * 76)
agg = collections.Counter()
aggw = collections.Counter()
for a, b in PAIRS:
    if not (os.path.isfile(os.path.join(ROOT, a)) and os.path.isfile(os.path.join(ROOT, b))):
        continue
    sa, sb = sections(os.path.join(ROOT, a)), sections(os.path.join(ROOT, b))
    print(f"\n── {a}  vs  {b}")
    keys = []
    for i in range(min(len(sa), len(sb))):
        (h1, t1), (h2, t2) = sa[i], sb[i]
        g1, g2 = ngrams(t1), ngrams(t2)
        if not g1 and not g2:
            continue
        inter = len(g1 & g2)
        ratio = inter / max(1, len(g1 | g2))
        dup = "🔴 完全重复" if ratio > 0.9 else ("🟠 高度重复" if ratio > 0.6 else
              ("🟡 部分重复" if ratio > 0.3 else "✅ 独有内容"))
        agg[ratio > 0.6] += 1
        aggw[ratio > 0.6] += len(t1.split())
        same_h = "" if h1 == h2 else f"  «标题不同: {h2[:30]}»"
        print(f"   {dup:10s} sim={ratio:.2f} 词数={len(t1.split()):4d}  {h1[:44]}{same_h}")
    # 未对齐的段（结构不同）
    if len(sa) != len(sb):
        print(f"   ⚠ 段落数不同 {a}={len(sa)} {b}={len(sb)}")
print("\n" + "=" * 76)
print(f"汇总：重复段(>0.6) {agg[True]} 个 / 独有段 {agg[False]} 个")
print(f"      重复段占正文词数 {aggw[True]*100//max(1,aggw[True]+aggw[False])}%")

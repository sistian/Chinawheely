#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给已插入的 CW:PRICE-LIST 区块补上结束标记（幂等）"""
import os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = "<!-- CW:PRICE-LIST -->"
END = "<!-- /CW:PRICE-LIST -->"

n = 0
for fn in sorted(os.listdir(BASE)):
    if not fn.endswith(".html"):
        continue
    p = os.path.join(BASE, fn)
    s = open(p, encoding="utf-8").read()
    if MARK not in s or END in s:
        continue
    # 结束点：优先用相邻注释；否则用价格区 </section> 之后的第一个 <!-- 或 <section
    cands = []
    for pat in ["<!-- Getting to ", "<!-- Travel Essentials -->", "<!-- Service CTA -->"]:
        i = s.find(pat, s.find(MARK))
        if i > 0:
            cands.append(i)
    if not cands:
        # 找价格区的结束 </section>（从 MARK 起第一个 section 结束标签之后）
        k = s.find(MARK)
        sec_start = s.find("<section", k)
        sec_end = s.find("</section>", sec_start)
        if sec_end < 0:
            continue
        at = sec_end + len("</section>")
        # 跳过后续空白
        while at < len(s) and s[at] in "\n ":
            at += 1
        s = s[:at] + END + "\n " + s[at:]
        open(p, "w", encoding="utf-8").write(s)
        n += 1
        continue
    at = min(cands)
    s = s[:at] + END + "\n " + s[at:]
    open(p, "w", encoding="utf-8").write(s)
    n += 1
print(f"补结束标记 {n} 页")

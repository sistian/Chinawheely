#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比 HEAD 与当前：整页近重复度是否因新增价格区块而升高"""
import os, re, subprocess, random
from itertools import combinations

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def toks_text(s):
    s = re.sub(r"<script.*?</script>", "", s, flags=re.S)
    s = re.sub(r"<style.*?</style>", "", s, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", s)
    return set(re.findall(r"[a-z]{4,}", t.lower()))


def head_text(f):
    r = subprocess.run(["git", "show", "HEAD:" + f], capture_output=True,
                       text=True, cwd=BASE)
    return toks_text(r.stdout) if r.returncode == 0 else None


files = []
for f in sorted(os.listdir(BASE)):
    if not f.endswith(".html"):
        continue
    s = open(os.path.join(BASE, f), encoding="utf-8", errors="ignore").read()
    if "CW:QUOTE-BLOCK" in s:
        files.append(f)

random.seed(1)
sample = random.sample(files, min(30, len(files)))

cur = {f: toks_text(open(os.path.join(BASE, f), encoding="utf-8", errors="ignore").read())
       for f in sample}
old = {f: head_text(f) for f in sample}

def jac(a, b):
    if not a or not b:
        return 0
    return len(a & b) / len(a | b)

deltas = []
for a, b in combinations(sample, 2):
    if old[a] is None or old[b] is None:
        continue
    deltas.append((jac(cur[a], cur[b]) - jac(old[a], old[b]), jac(old[a], old[b]), jac(cur[a], cur[b]), a, b))

deltas.sort(reverse=True)
print(f"{'Δ':>7}  {'旧':>6}  {'新':>6}   页面对")
for d, o, n, a, b in deltas[:8]:
    print(f"{d:+7.3f}  {o:6.3f}  {n:6.3f}   {a} / {b}")
print("...")
for d, o, n, a, b in deltas[-5:]:
    print(f"{d:+7.3f}  {o:6.3f}  {n:6.3f}   {a} / {b}")
avg = sum(d for d, *_ in deltas) / len(deltas)
print(f"\n平均近重复度变化: {avg:+.4f}  (样本 {len(deltas)} 对)")
print(f"当前平均相似度: {sum(x[2] for x in deltas)/len(deltas):.3f}")
print(f"修改前平均相似度: {sum(x[1] for x in deltas)/len(deltas):.3f}")

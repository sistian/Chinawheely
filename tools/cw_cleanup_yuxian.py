#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理玉溪重复页 yuxian（保留 yuxi）
- 删 yuxian.html 及其专属图片
- pricing/pricing.json: 去掉 karakax / yuxian 残留映射，修正 cityCount
- prices.html: JSON-LD ItemList 去掉 karakax / yuxian 并重排 position
- 全站校验：0 引用残留
幂等：可重复执行
"""
import json, os, re, glob, sys

REPO = "/Users/w/Desktop/Chinawheely 10.27"
DEAD = ["karakax", "yuxian"]

def read(p):
    return open(p, encoding="utf-8").read()

def write(p, t):
    open(p, "w", encoding="utf-8").write(t)

report = []

# ---------- 1. 删页面 ----------
page = os.path.join(REPO, "yuxian.html")
if os.path.exists(page):
    os.remove(page)
    report.append("deleted yuxian.html")

# ---------- 2. 删专属图片（只删 yuxian 前缀，避免误删 yuxi） ----------
removed_imgs = []
for p in glob.glob(os.path.join(REPO, "images", "yuxian*")):
    os.remove(p)
    removed_imgs.append(os.path.basename(p))
if removed_imgs:
    report.append("deleted images: " + ", ".join(sorted(removed_imgs)))

# ---------- 3. pricing.json ----------
pj = os.path.join(REPO, "pricing", "pricing.json")
data = json.loads(read(pj))
cnt_before = data.get("cityCount")
# 顶层可能存在 city -> price 的映射 dict
def strip_dead(obj, path="root"):
    n = 0
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            if k in DEAD:
                del obj[k]
                n += 1
            else:
                n += strip_dead(obj[k], path + "." + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            n += strip_dead(v, path + "[%d]" % i)
    return n

n_removed = strip_dead(data)
# cityCount 修正为实际城市数
def find_city_map(d):
    """找形如 {slug: {...price...}} 的最大 dict"""
    best = None
    def walk(o, p=""):
        nonlocal best
        if isinstance(o, dict):
            if o and all(isinstance(v, dict) for v in o.values()) and len(o) > 50:
                if best is None or len(o) > len(best[1]):
                    best = (p, o)
            for k, v in o.items():
                walk(v, p + "." + str(k))
    walk(d)
    return best

cm = find_city_map(data)
actual = len(cm[1]) if cm else None
if actual is not None:
    data["cityCount"] = actual
write(pj, json.dumps(data, ensure_ascii=False, indent=2))
report.append("pricing.json: removed %d dead keys, cityCount %s -> %s (map=%s)" % (n_removed, cnt_before, data["cityCount"], cm[0] if cm else "?"))

# ---------- 4. prices.html JSON-LD ItemList ----------
ph = os.path.join(REPO, "prices.html")
h = read(ph)
before = h

def fix_itemlist(m):
    block = m.group(0)
    items = re.findall(r'\{"@type": "ListItem", "position": \d+, "name": ".*?", "url": ".*?"\}', block)
    kept = [it for it in items if not any(("/%s.html" % d) in it for d in DEAD)]
    if len(kept) == len(items):
        return block
    out = []
    for i, it in enumerate(kept, 1):
        out.append(re.sub(r'"position": \d+', '"position": %d' % i, it))
    return block[:m.start(0) - m.start(0)] + "[" + ", ".join(out) + "]" if False else re.sub(r'\[\{"@type": "ListItem".*?\}\]', "[" + ", ".join(out) + "]", block, flags=re.S)

h2 = re.sub(r'\[\{"@type": "ListItem".*?\}\]', fix_itemlist, h, count=1, flags=re.S)
if h2 != before:
    write(ph, h2)
    report.append("prices.html: JSON-LD ItemList 去重并重排 position")

# ---------- 5. 全站校验残留 ----------
leftovers = []
for root, dirs, files in os.walk(REPO):
    if ".git" in root or "/node_modules" in root:
        continue
    for f in files:
        if not f.endswith((".html", ".xml", ".json", ".js")):
            continue
        p = os.path.join(root, f)
        try:
            t = read(p)
        except Exception:
            continue
        for d in DEAD:
            if d in t:
                leftovers.append((os.path.relpath(p, REPO), d))

print("== 清理报告 ==")
for r in report:
    print(" -", r)
print("\n== 残留检查 ==")
if leftovers:
    for f, d in leftovers:
        print("  !", f, "含", d)
else:
    print("  全站 0 残留（html/xml/json/js）")

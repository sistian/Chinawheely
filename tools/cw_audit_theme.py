#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主题页质量体检（独立门禁，供 cw_audit.py 之后运行）
检查：
 1. 每页正文词数达标
 2. 同族页两两 5-gram 相似度中位数上限（防模板重复）
 3. 每页 h2 数量（内容层次）
 4. 无 seo-keywords 关键词堆砌块
 5. 有 <main> 地标
 6. JSON-LD 块数 ≥ 4 且全部合法
 7. canonical 与 og:url 一致
 8. 页面间重复句（≥12 词连续相同）计数
"""
import json, os, re, sys, itertools, collections

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

FAMS = ['best-time', 'day-trips', 'photo-spots', 'food-shopping', 'tea-culture']
MIN_WORDS = {'airport': 700, 'day-trips': 600, 'photo-spots': 600,
             'food-shopping': 550, 'tea-culture': 500}
SIM_MAX = 0.40          # 同族两页 5-gram 相似度中位数上限
DUP_SENTENCE_WORDS = 12

results = []


def add(lvl, name, detail):
    results.append((lvl, name, detail))


def body_of(h):
    h = re.sub(r'<script.*?</script>', '', h, flags=re.S | re.I)
    h = re.sub(r'<style.*?</style>', '', h, flags=re.S | re.I)
    h = re.sub(r'<!--.*?-->', '', h, flags=re.S)
    m = re.search(r'<main\b.*?>(.*?)</main>', h, re.S | re.I)
    b = m.group(1) if m else h
    b = re.sub(r'<nav.*?</nav>', '', b, flags=re.S | re.I)
    b = re.sub(r'<footer.*?</footer>', '', b, flags=re.S | re.I)
    # 剥掉全站通用骨架，只量“正文内容”本身的重复度
    b = re.sub(r'<section class="hero[^"]*".*?</section>', '', b, flags=re.S | re.I)
    b = re.sub(r'<div class="page-head-links".*?</div>\s*</div>', '', b, flags=re.S | re.I)
    b = re.sub(r'<div class="page-siblings".*?</div>\s*</div>', '', b, flags=re.S | re.I)
    b = re.sub(r'<div class="seo-keywords".*?</div>', '', b, flags=re.S | re.I)
    return b


def text_of(b):
    t = re.sub(r'<[^>]+>', ' ', b)
    return re.sub(r'\s+', ' ', t).strip()


def shingles(t, n=5):
    w = t.split()
    return set(tuple(w[i:i + n]) for i in range(len(w) - n + 1))


theme = []
for f in sorted(os.listdir('.')):
    if not f.endswith('.html'):
        continue
    s = f[:-5]
    fam = None
    for x in FAMS:
        if s.endswith('-' + x):
            fam = x
    if '-airport-transfer-to-' in s:
        fam = 'airport'
    if fam:
        theme.append((f, fam))
print(f'主题页 {len(theme)} 个')

# 1 词数
thin = []
data = {}
for f, fam in theme:
    h = open(f, encoding='utf-8', errors='ignore').read()
    b = body_of(h)
    t = text_of(b)
    data[f] = (fam, t, h)
    if len(t.split()) < MIN_WORDS.get(fam, 500):
        thin.append(f'{f}({len(t.split())})')
if thin:
    add('FAIL', '主题页:正文词数', f'{len(thin)} 页低于阈值 {thin[:6]}')
else:
    add('PASS', '主题页:正文词数', f'{len(theme)} 页全部达标 '
                f'(airport≥{MIN_WORDS["airport"]}, day/photo≥600, food≥550, tea≥500)')

# 2 同族相似度
byfam = collections.defaultdict(list)
for f, fam in theme:
    byfam[fam].append(f)
sim_bad = []
for fam, fs in byfam.items():
    if len(fs) < 2:
        continue
    sh = {f: shingles(data[f][1]) for f in fs}
    best = []
    for a, b in itertools.combinations(fs, 2):
        A, B = sh[a], sh[b]
        if not A or not B:
            continue
        best.append(len(A & B) / min(len(A), len(B)))
    if not best:
        continue
    best.sort()
    med = best[len(best) // 2]
    if med > SIM_MAX:
        sim_bad.append(f'{fam}中位{med:.2f}')
    print(f'  {fam:16s} 页对 {len(best):4d}  中位相似 {med:.3f}  最高 {best[-1]:.3f}')
if sim_bad:
    add('FAIL', '主题页:同族重复度', f'中位相似度超 {SIM_MAX}  {" ".join(sim_bad)}')
else:
    add('PASS', '主题页:同族重复度', f'各族中位相似度均 ≤ {SIM_MAX}')

# 3 h2 数量
few_h2 = [f for f, fam in theme if len(re.findall(r'<h2\b', data[f][2], re.I)) < 4]
if few_h2:
    add('FAIL', '主题页:内容层次', f'{len(few_h2)} 页 h2 < 4  {few_h2[:6]}')
else:
    add('PASS', '主题页:内容层次', '每页 h2 ≥ 4')

# 4 seo-keywords 堆砌块
sk = [f for f in data if 'seo-keywords' in data[f][2]]
if sk:
    add('FAIL', '主题页:关键词堆砌块', f'{len(sk)} 页仍含 seo-keywords  {sk[:6]}')
else:
    add('PASS', '主题页:关键词堆砌块', '0 页含 seo-keywords 块')

# 5 <main>
nm = [f for f in data if '<main' not in data[f][2]]
if nm:
    add('FAIL', '主题页:main 地标', f'{len(nm)} 页缺 <main>  {nm[:6]}')
else:
    add('PASS', '主题页:main 地标', '全部有 <main>')

# 6 JSON-LD
bad_ld = []
few_ld = []
for f in data:
    h = data[f][2]
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
    if len(blocks) < 4:
        few_ld.append(f'{f}({len(blocks)})')
    for b in blocks:
        try:
            json.loads(b)
        except Exception:
            bad_ld.append(f)
if bad_ld:
    add('FAIL', '主题页:JSON-LD 合法', f'{len(bad_ld)} 块非法 {bad_ld[:5]}')
elif few_ld:
    add('WARN', '主题页:JSON-LD 数量', f'{len(few_ld)} 页 <4 块 {few_ld[:6]}')
else:
    add('PASS', '主题页:JSON-LD', '全部合法且 ≥4 块/页')

# 7 canonical vs og:url
mismatch = []
for f in data:
    h = data[f][2]
    c = re.search(r'<link rel="canonical" href="([^"]*)"', h)
    o = re.search(r'<meta property="og:url" content="([^"]*)"', h)
    if not c or not o:
        mismatch.append(f'{f}(缺)')
    elif c.group(1).rstrip('/') != o.group(1).rstrip('/'):
        mismatch.append(f)
if mismatch:
    add('FAIL', '主题页:canonical/og:url', f'{len(mismatch)} 页不一致 {mismatch[:6]}')
else:
    add('PASS', '主题页:canonical/og:url', '全部一致')

# 8 重复句（≥12 词连续相同，跨页）
sent = collections.defaultdict(set)
for f in data:
    t = data[f][1]
    for s in re.split(r'(?<=[.!?])\s+', t):
        w = s.split()
        if len(w) >= DUP_SENTENCE_WORDS:
            sent[' '.join(w[:DUP_SENTENCE_WORDS])].add(f)
dup = {k: v for k, v in sent.items() if len(v) > 1}
if dup:
    add('FAIL', '主题页:跨页重复句', f'{len(dup)} 句在多页重复  {list(dup)[:2]}')
else:
    add('PASS', '主题页:跨页重复句', '无 ≥12 词跨页重复句')

# ---------- 输出 ----------
print("=" * 78)
for lvl, name, detail in sorted(results, key=lambda r: {'FAIL': 0, 'WARN': 1, 'PASS': 2}[r[0]]):
    print(f"[{lvl}] {name:22} {detail}")
f = sum(1 for r in results if r[0] == 'FAIL')
w = sum(1 for r in results if r[0] == 'WARN')
print("=" * 78)
print(f"FAIL {f} | WARN {w} | PASS {len(results)-f-w}")
sys.exit(1 if f else 0)

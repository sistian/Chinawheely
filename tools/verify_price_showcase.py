#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P5 综合验收：报价展示层全链路自检"""
import json, os, re, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, "pricing", "pricing.json"), encoding="utf-8"))
C = d["cities"]
R = d["meta"]["usdCnyRate"]

fails, warns = [], []


def chk(cond, msg):
    if cond:
        print(f"  ✅ {msg}")
    else:
        fails.append(msg)
        print(f"  ❌ {msg}")


def head(f):
    r = subprocess.run(["git", "show", "HEAD:" + f], capture_output=True,
                       text=True, cwd=BASE)
    return r.stdout if r.returncode == 0 else ""


print("=" * 68)
print("P5 报价展示层验收")
print("=" * 68)

# 1. 首页航线价格
print("\n【1】首页具名航线价格")
s = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
routes = re.findall(r'class="route-price">\s*(.*?)\s*</div>', s)
exp = [("Beijing Capital (PEK)", "beijing"), ("Shanghai Pudong (PVG)", "shanghai"),
       ("Chengdu Tianfu (TFU)", "chengdu")]
for (label, slug), got in zip(exp, routes):
    c = C[slug]
    p = min(v["pkg"] for v in c["airport"].values())
    want = f"From ¥{p} (≈ ${round(p / R, 2)})"
    chk(got == want, f"{label} → {got}")

# 2. 首页定价卡片无占位价
print("\n【2】首页 Transparent Pricing 卡片")
i = s.find('id="pricing"')
seg = s[i:i + 3000]
cards = re.findall(r'pricing-price">(.*?)</div>\s*</div>', seg, re.S)
for c_ in cards:
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c_)).strip()
    chk("$50" not in txt and "$80" not in txt and "$105" not in txt,
        f"卡片无占位价: {txt[:70]}")

# 3. 首页定价模型段落已去伪存真
print("\n【3】首页定价模型段落")
chk("Smart Distance Pricing" not in s, "已删除虚构的距离分档定价段落")
chk("Transparent Pricing" in s, "首页保留真实口径定价区")
chk("across all 331 cities" in s, "定价区已标注 331 城口径")
chk("$50" not in s and "$90" not in s and "$125" not in s,
    "首页不再出现虚构的分档价 $50/$90/$125")

# 4. 首页优势区
print("\n【4】首页优势卖点区")
chk("CW:WHY-ADV" in s, "首页已插入 Why Chinawheely 优势区")
chk(s.count("adv-card") >= 6, f"优势卡片 {s.count('adv-card')//2} 张")

# 5. 城市页区块覆盖
print("\n【5】城市页价格区块覆盖")
pl, qb = [], []
for fn in sorted(os.listdir(BASE)):
    if not fn.endswith(".html"):
        continue
    t = open(os.path.join(BASE, fn), encoding="utf-8", errors="ignore").read()
    if "CW:PRICE-LIST" in t:
        pl.append(fn)
    if "CW:QUOTE-BLOCK" in t:
        qb.append(fn)
# 期望值从 pricing.json 动态推导（331 城全覆盖后不再写死数字）
PRICED = set(json.load(open(os.path.join(BASE, 'pricing', 'pricing.json'), encoding='utf-8'))['cities'])
pl_slugs = {f[:-5] for f in pl}
qb_slugs = {f[:-5] for f in qb}
missing = sorted(PRICED - pl_slugs)
chk(not missing, f"有价城市均已插入真实价目表（缺 {len(missing)}：{missing[:5]}）")
chk(not (qb_slugs & PRICED), f"询价区块与有价城市互斥（重叠 {len(qb_slugs & PRICED)}）")
chk(len(pl) >= len(PRICED), f"真实价目表页 {len(pl)} 个（应 ≥ {len(PRICED)}）")
chk(len(set(pl) & set(qb)) == 0, "两区块互斥，无重复")

# 6. 区块完整性
print("\n【6】区块完整性")
bad_end = [f for f in pl + qb
           if "<!-- /CW:PRICE-LIST -->" not in
           open(os.path.join(BASE, f), encoding="utf-8", errors="ignore").read()
           and "<!-- /CW:QUOTE-BLOCK -->" not in
           open(os.path.join(BASE, f), encoding="utf-8", errors="ignore").read()]
chk(not bad_end, f"所有区块有结束标记（异常 {len(bad_end)}）")

bad_bal = []
for f in pl + qb:
    t = open(os.path.join(BASE, f), encoding="utf-8", errors="ignore").read()
    i = t.find("<!-- CW:")
    j = t.find("<!-- /CW:", i)
    blk = t[i:j]
    for tag in ["div", "section", "table", "tbody", "thead", "tr", "ul", "li"]:
        o = len(re.findall(r"<%s[\s>]" % tag, blk))
        c = len(re.findall(r"</%s>" % tag, blk))
        if o != c:
            bad_bal.append((f, tag))
            break
chk(not bad_bal, f"区块标签平衡（异常 {len(bad_bal)}）")

# 7. 无二次转义
print("\n【7】HTML 实体")
bad_ent = []
for f in pl + qb:
    t = open(os.path.join(BASE, f), encoding="utf-8", errors="ignore").read()
    for e in ["&amp;mdash;", "&amp;yen;", "&amp;nbsp;", "&amp;amp;"]:
        if e in t:
            bad_ent.append((f, e))
chk(not bad_ent, f"无实体二次转义（异常 {len(bad_ent)}）")

# 8. 真实价目表逐格核对
print("\n【8】真实价目表逐格核对")
cells = 0
mismatch = []
for fn in pl:
    slug = fn[:-5]
    c = C.get(slug) or C.get({"huhehaote": "hohhot"}.get(slug, "")) or C.get({"hohhot": "huhehaote"}.get(slug, ""))
    if not c:
        continue
    t = open(os.path.join(BASE, fn), encoding="utf-8", errors="ignore").read()
    i = t.find("<!-- CW:PRICE-LIST -->")
    j = t.find("<!-- /CW:PRICE-LIST -->", i)
    blk = t[i:j]
    apt = blk[blk.find("Airport &amp; Intercity Transfer"):blk.find("Hourly Private Charter")]
    for name, seats, bags, p, u, pm, pk in re.findall(
            r'<tr><td><strong>(.*?)</strong></td><td>(\d+)</td><td>(\d+)</td>'
            r'<td class="pl-price">¥([\d,]+)</td><td class="pl-usd">≈ \$([\d.]+)</td>'
            r'<td class="pl-rate">¥([\d.]+)/min · ¥([\d.]+)/km</td></tr>', apt):
        e = next((v for v in c["airport"].values() if v["name"] == name), None)
        if not e:
            mismatch.append((fn, name))
            continue
        cells += 1
        if (int(p.replace(",", "")), float(u), float(pm), float(pk), int(seats), int(bags)) != \
           (e["pkg"], round(e["pkg"] / R, 2), e["perMin"], e["perKm"], e["seats"], e["bags"]):
            mismatch.append((fn, name))
    order = ["2h_35km", "4h_50km", "6h_75km", "8h_100km", "10h_125km"]
    cht = blk[blk.find("Hourly Private Charter"):]
    cht = cht[:cht.find("</table>")]
    for name, cellsx in re.findall(
            r'<tr><td><strong>(.*?)</strong></td>((?:<td[^>]*>¥[\d,]+</td>|<td>—</td>){5})</tr>', cht):
        e = next((v for v in c["charter"].values() if v["name"] == name), None)
        if not e:
            mismatch.append((fn, name))
            continue
        cells += 1
        got = [int(x.replace(",", "")) for x in re.findall(r"¥([\d,]+)", cellsx)]
        exp_ = [e["tiers"][t_]["pkg"] for t_ in order]
        if got != exp_:
            mismatch.append((fn, name))
chk(not mismatch, f"{cells} 个价格单元与报价单严格一致（不一致 {len(mismatch)}）")

# 9. 日游价格 bug
print("\n【9】日游卡价格（曾错按机场价计）")
fixed = 0
still = []
for fn in pl:
    t = open(os.path.join(BASE, fn), encoding="utf-8", errors="ignore").read()
    slug = fn[:-5]
    c = C.get(slug) or C.get({"huhehaote": "hohhot"}.get(slug, "")) or C.get({"hohhot": "huhehaote"}.get(slug, ""))
    if not c:
        continue
    eco = c["airport"]["sedan_economy"]["pkg"]
    ch8 = c["charter"]["sedan_4"]["tiers"]["8h_100km"]["pkg"]
    m = re.search(r"Day Trips from [A-Za-z ]*?</h2>(.*?)</section>", t, re.S)
    if not m:
        continue
    for mm in re.finditer(r"<h4[^>]*>.*?</h4>(.{0,700}?)From ¥([\d,]+)", m.group(1), re.S):
        body = re.sub(r"<[^>]+>", " ", mm.group(1))
        shown = int(mm.group(2).replace(",", ""))
        if re.search(r"\d+\s*-?\s*hours?", body, re.I):
            continue
        if re.search(r"day itinerary|day trip|full-day|full day|day tour|day pass", body, re.I):
            if shown == eco and eco != ch8:
                still.append((fn, shown, ch8))
            elif shown == ch8:
                fixed += 1
chk(not still, f"日游卡不再错按机场价（已修正 {fixed} 处，仍错 {len(still)}）")

# 10. 无价城市块文案个性化
print("\n【10】询价区块个性化")
noprov = []
for fn in qb:
    t = open(os.path.join(BASE, fn), encoding="utf-8", errors="ignore").read()
    m = re.search(r'<h2[^>]*>What Your ([^<]+?) Ride Will Cost</h2>', t)
    if not m or "(" not in m.group(1):
        noprov.append(fn)
chk(not noprov, f"每个询价页标题均带省份（异常 {len(noprov)}）")

# 11. 无价城市不出现假价
print("\n【11】无价城市不出现假价")
fake = []
for fn in qb:
    t = open(os.path.join(BASE, fn), encoding="utf-8", errors="ignore").read()
    i = t.find("<!-- CW:QUOTE-BLOCK -->")
    j = t.find("<!-- /CW:QUOTE-BLOCK -->", i)
    blk = t[i:j]
    # 只允许出现参照表里的真实城市价
    for m in re.finditer(r'<td class="qb-price">¥([\d,]+)</td>', blk):
        v = int(m.group(1).replace(",", ""))
        if v not in {c["airport"]["sedan_economy"]["pkg"] for c in C.values()}:
            fake.append((fn, v))
chk(not fake, f"参照表价格均来自报价单（异常 {len(fake)}）")

# 12. CSS 已就位
print("\n【12】样式")
css = open(os.path.join(BASE, "styles.css"), encoding="utf-8").read()
for cls in [".pl-cols", ".pl-table", ".adv-grid", ".adv-card", ".qb-list", ".qb-price", ".pl-cta"]:
    chk(cls in css, f"styles.css 含 {cls}")

print("\n" + "=" * 68)
if fails:
    print(f"❌ 失败 {len(fails)} 项：")
    for f_ in fails:
        print("   -", f_)
    sys.exit(1)
print("✅ 全部通过")

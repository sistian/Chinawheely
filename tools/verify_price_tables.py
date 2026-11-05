#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐页核对 CW:PRICE-LIST 区块里的每一个 ¥ 与 ≈$ 是否与 pricing.json 严格一致"""
import json, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, "pricing", "pricing.json"), encoding="utf-8"))
C = d["cities"]
R = d["meta"]["usdCnyRate"]
ALIAS = {"huhehaote": "hohhot"}

errs = []
checked_pages = 0
checked_cells = 0

for fn in sorted(os.listdir(BASE)):
    if not fn.endswith(".html"):
        continue
    slug = fn[:-5]
    c = C.get(slug) or C.get(ALIAS.get(slug, ""))
    if not c:
        continue
    s = open(os.path.join(BASE, fn), encoding="utf-8").read()
    if "<!-- CW:PRICE-LIST -->" not in s:
        continue
    i = s.find("<!-- CW:PRICE-LIST -->")
    j = s.find("<!-- /CW:PRICE-LIST -->", i)
    blk = s[i:j]
    checked_pages += 1

    # --- 机场/城际表 ---
    ap_i = blk.find("Airport &amp; Intercity Transfer")
    ap_j = blk.find("Hourly Private Charter")
    aptbl = blk[ap_i:ap_j]
    rows = re.findall(
        r'<tr><td><strong>(.*?)</strong></td><td>(\d+)</td><td>(\d+)</td>'
        r'<td class="pl-price">¥([\d,]+)</td><td class="pl-usd">≈ \$([\d.]+)</td>'
        r'<td class="pl-rate">¥([\d.]+)/min · ¥([\d.]+)/km</td></tr>', aptbl)
    if len(rows) != len(c["airport"]):
        errs.append((fn, f"机场表行数 {len(rows)} != pricing {len(c['airport'])}"))
    for name, seats, bags, p, u, pm, pk in rows:
        key = next((k for k, v in c["airport"].items() if v["name"] == name), None)
        if not key:
            errs.append((fn, f"未知车型 {name}"))
            continue
        e = c["airport"][key]
        got = (int(p.replace(",", "")), float(u), float(pm), float(pk),
               int(seats), int(bags))
        exp = (e["pkg"], round(e["pkg"] / R, 2), e["perMin"], e["perKm"],
               e["seats"], e["bags"])
        checked_cells += 1
        if got != exp:
            errs.append((fn, f"机场 {name}: got={got} exp={exp}"))

    # --- 包车档位表 ---
    ch_i = blk.find("Hourly Private Charter")
    chtbl = blk[ch_i:chtbl_end] if False else blk[ch_i:]
    chtbl = chtbl[:chtbl.find("</table>")]
    order = ["2h_35km", "4h_50km", "6h_75km", "8h_100km", "10h_125km"]
    crows = re.findall(
        r'<tr><td><strong>(.*?)</strong></td>((?:<td[^>]*>¥[\d,]+</td>|<td>—</td>){5})</tr>',
        chtbl)
    if len(crows) != len(c["charter"]):
        errs.append((fn, f"包车表行数 {len(crows)} != pricing {len(c['charter'])}"))
    for name, cells in crows:
        key = next((k for k, v in c["charter"].items() if v["name"] == name), None)
        if not key:
            errs.append((fn, f"未知包车车型 {name}"))
            continue
        got = [int(x.replace(",", "")) for x in re.findall(r"¥([\d,]+)", cells)]
        exp = [c["charter"][key]["tiers"][t]["pkg"] for t in order]
        checked_cells += 1
        if got != exp:
            errs.append((fn, f"包车 {name}: got={got} exp={exp}"))

print(f"核对 {checked_pages} 个城市页 / {checked_cells} 个价格单元")
if errs:
    print(f"❌ 不一致 {len(errs)} 处")
    for e in errs[:20]:
        print("   ", e)
    sys.exit(1)
print("✅ 全部与 pricing.json 严格一致")

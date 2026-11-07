#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立校验 pricing.json 是否严格等于「更新版 Excel 显式值优先 + 仅从参照城补 '-' 单元格」策略。
不复用 gen_pricing.py 的填充逻辑，而是从 xlsx 重新独立推导一遍再比对，
避免「生成器与校验器互相印证」的假阳性。

用法：python3 tools/verify_pricing_vs_xlsx.py
"""
import json, os, re, sys

import openpyxl

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.join(BASE, "pricing", "source",
                    "入境游包车报价单_游客版 2026年 报价单 更新版本.xlsx")

# ---- 与报价单结构一致的常量（取自 gen_pricing.py，但这里独立写一遍）----
AIRPORT_VEHICLES = [
    ("sedan_economy", "4座 经济型专车", 4, 3),
    ("sedan_comfort", "4座 舒适型专车", 4, 3),
    ("mpv_6", "6座 商务车", 6, 4),
    ("van_8_11", "8-11座 商务车", 8, 6),
    ("van_12_18", "12-18座 商务车", 12, 8),
    ("coach_19_55", "19-55座 大巴", 19, 12),
]
CHARTER_SHEETS = [
    ("4座专车报价", "sedan_4", "4座 专车", 4, 2),
    ("6座商务车报价", "mpv_6", "6座 商务车", 6, 4),
    ("8-11座车报价", "van_8_11", "8-11座 商务车", 8, 6),
    ("12-18座车报价", "van_12_18", "12-18座 商务车", 12, 8),
    ("19-55座车报价", "coach_19_55", "19-55座 大巴", 19, 12),
]
TIERS = [("2h_35km", 2, 35), ("4h_50km", 4, 50), ("6h_75km", 6, 75),
         ("8h_100km", 8, 100), ("10h_125km", 10, 125)]
FILL_FROM = {"yinchuan": "weihai", "taizhou": "jiaxing"}
SLUG_OVERRIDE = {"xi'an": "xian"}


def slugify(s):
    return SLUG_OVERRIDE.get(s.strip().lower().replace("'", ""),
                             s.strip().lower().replace("'", ""))


def num(v):
    return v if isinstance(v, (int, float)) else None


def read_cell(ws, r, c):
    v = ws.cell(row=r, column=c).value
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip().replace(",", "")
        if v in ("", "-", "—", "/"):
            return None
        try:
            v = float(v)
        except ValueError:
            return None
    return v


def build_from_xlsx():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    cities = {}

    # ---- 接送机表 ----
    ws = wb["各种车型接送机报价"]
    for r in range(2, ws.max_row + 1):
        label = ws.cell(row=r, column=1).value
        if not label:
            continue
        m = re.match(r"^(.+?市)\s+([A-Za-z' ]+)$", str(label).strip())
        if not m:
            continue
        cn, en = m.group(1), m.group(2).strip()
        slug = slugify(en)
        c = cities.setdefault(slug, {"cn": cn, "en": en, "airport": {}, "charter": {}})
        for vi, (vkey, vname, seats, bags) in enumerate(AIRPORT_VEHICLES):
            base = 2 + vi * 5
            pkg = num(read_cell(ws, r, base))
            if pkg is None:
                continue
            c["airport"][vkey] = {
                "name": vname, "seats": seats, "bags": bags,
                "pkg": pkg,
                "perMin": num(read_cell(ws, r, base + 1)),
                "perKm": num(read_cell(ws, r, base + 3)),
            }

    # ---- 包车表 ----
    for sheet, vkey, vname, seats, bags in CHARTER_SHEETS:
        ws = wb[sheet]
        for r in range(2, ws.max_row + 1):
            label = ws.cell(row=r, column=1).value
            if not label:
                continue
            m = re.match(r"^(.+?市)\s+([A-Za-z' ]+)$", str(label).strip())
            if not m:
                continue
            cn, en = m.group(1), m.group(2).strip()
            slug = slugify(en)
            c = cities.setdefault(slug, {"cn": cn, "en": en, "airport": {}, "charter": {}})
            tiers = {}
            for ti, (tkey, hrs, km) in enumerate(TIERS):
                base = 2 + ti * 3
                pkg = num(read_cell(ws, r, base))
                if pkg is None:
                    continue
                tiers[tkey] = {
                    "hours": hrs, "includedKm": km, "pkg": pkg,
                    "perMin": num(read_cell(ws, r, base + 1)),
                    "perKm": num(read_cell(ws, r, base + 2)),
                }
            if tiers:
                c["charter"][vkey] = {"name": vname, "seats": seats, "bags": bags, "tiers": tiers}
    return cities


def apply_fill(cities):
    """显式值优先：仅当目标格为 None（xlsx 里是 '-'）才从参照城补同位"""
    log = []
    for target, src in FILL_FROM.items():
        t, s = cities.get(target), cities.get(src)
        if not t or not s:
            log.append((target, src, "SKIP", "城市缺失"))
            continue
        n = 0
        for vkey, sv in s["airport"].items():
            tv = t["airport"].get(vkey)
            if tv is None:
                t["airport"][vkey] = json.loads(json.dumps(sv)); n += 1
                continue
            for f in ("pkg", "perMin", "perKm"):
                if tv.get(f) is None and sv.get(f) is not None:
                    tv[f] = sv[f]; n += 1
        for vkey, sv in s["charter"].items():
            tv = t["charter"].get(vkey)
            if tv is None:
                t["charter"][vkey] = json.loads(json.dumps(sv)); n += 1
                continue
            for tkey, stv in sv["tiers"].items():
                ttv = tv["tiers"].get(tkey)
                if ttv is None:
                    tv["tiers"][tkey] = json.loads(json.dumps(stv)); n += 1
                    continue
                for f in ("pkg", "perMin", "perKm"):
                    if ttv.get(f) is None and stv.get(f) is not None:
                        ttv[f] = stv[f]; n += 1
        log.append((target, src, n, ""))
    return cities, log


def main():
    expected = build_from_xlsx()
    expected, fill_log = apply_fill(expected)

    actual = json.load(open(os.path.join(BASE, "pricing", "pricing.json"), encoding="utf-8"))
    A = actual["cities"]
    # 2026-11-07 起键名统一为站点 slug：hohhot→huhehaote（同一城市）
    if "hohhot" in expected and "huhehaote" in A:
        expected["huhehaote"] = expected.pop("hohhot")

    print("=" * 70)
    print("pricing.json ← xlsx 独立重算校验（策略：显式值优先，仅补 '-'）")
    print("=" * 70)

    # 1) 城市集合
    e, a = set(expected), set(A)
    print(f"\n【1】城市集合")
    if e - a:
        print(f"  ❌ pricing.json 缺 {sorted(e - a)}")
        return 1
    if a - e:
        print(f"  ⚠️  pricing.json 多 {sorted(a - e)}")
    print(f"  ✅ xlsx {len(e)} 城 = pricing.json {len(a)} 城")

    # 2) 逐格比对
    diffs = []
    checked = 0
    for slug in sorted(e & a):
        ec, ac = expected[slug], A[slug]
        for vkey in set(ec["airport"]) | set(ac["airport"]):
            ev, av = ec["airport"].get(vkey), ac["airport"].get(vkey)
            if not ev or not av:
                diffs.append((slug, f"airport.{vkey}", "缺失"))
                continue
            for f in ("pkg", "perMin", "perKm"):
                checked += 1
                if ev.get(f) != av.get(f):
                    diffs.append((slug, f"airport.{vkey}.{f}", f"xlsx={ev.get(f)} json={av.get(f)}"))
        for vkey in set(ec["charter"]) | set(ac["charter"]):
            ev, av = ec["charter"].get(vkey), ac["charter"].get(vkey)
            if not ev or not av:
                diffs.append((slug, f"charter.{vkey}", "缺失"))
                continue
            for tkey in set(ev["tiers"]) | set(av["tiers"]):
                et, at = ev["tiers"].get(tkey), av["tiers"].get(tkey)
                if not et or not at:
                    diffs.append((slug, f"charter.{vkey}.{tkey}", "缺失"))
                    continue
                for f in ("pkg", "perMin", "perKm"):
                    checked += 1
                    if et.get(f) != at.get(f):
                        diffs.append((slug, f"charter.{vkey}.{tkey}.{f}",
                                       f"xlsx={et.get(f)} json={at.get(f)}"))
    print(f"\n【2】价格单元逐格比对：{checked} 格")
    if diffs:
        print(f"  ❌ {len(diffs)} 处不一致：")
        for d in diffs[:25]:
            print("     ", d)
    else:
        print(f"  ✅ 全部一致")

    # 3) 显式值优先的证据：银川/台州 哪些格是显式、哪些是补的
    print(f"\n【3】银川/台州 单元格级口径")
    for target, src in FILL_FROM.items():
        print(f"  --- {target} ← {src} ---")
        ec, sc = expected[target], expected[src]
        # 用「补全前的原始 xlsx 值」来判定
        raw = build_from_xlsx()
        rt = raw[target]
        filled_cells, explicit_cells = [], []
        for vkey in rt["airport"]:
            for f in ("pkg", "perMin", "perKm"):
                v = rt["airport"][vkey].get(f)
                sv = sc["airport"].get(vkey, {}).get(f) if vkey in sc["airport"] else None
                (explicit_cells if v is not None else filled_cells).append(
                    f"airport.{vkey}.{f}={v if v is not None else sv}")
        for vkey, tv in rt["charter"].items():
            for tkey, ttv in tv["tiers"].items():
                for f in ("pkg", "perMin", "perKm"):
                    v = ttv.get(f)
                    sv = sc["charter"].get(vkey, {}).get("tiers", {}).get(tkey, {}).get(f)
                    (explicit_cells if v is not None else filled_cells).append(
                        f"charter.{vkey}.{tkey}.{f}={v if v is not None else sv}")
        print(f"    显式值（xlsx 有数字）{len(explicit_cells)} 格")
        print(f"    从参照城补 '-'     {len(filled_cells)} 格")
        for c in explicit_cells[:8]:
            print(f"      显式  {c}")
        print(f"      ... 共 {len(explicit_cells)} 格显式")
        for c in filled_cells[:5]:
            print(f"      补全  {c}")
        print(f"      ... 共 {len(filled_cells)} 格补全")

    # 4) 与参照城是否「整城同价」
    print(f"\n【4】是否被误做成「整城同价」（应全部为否）")
    for target, src in FILL_FROM.items():
        same = A[target]["airport"]["sedan_economy"]["pkg"] == A[src]["airport"]["sedan_economy"]["pkg"]
        print(f"  {'❌' if same else '✅'} {target} 经济型接送 ¥{A[target]['airport']['sedan_economy']['pkg']}"
              f" vs {src} ¥{A[src]['airport']['sedan_economy']['pkg']} → {'整城同价' if same else '不同价（正确）'}")
        t19 = A[target]["charter"]["coach_19_55"]["tiers"]["2h_35km"]["pkg"]
        s19 = A[src]["charter"]["coach_19_55"]["tiers"]["2h_35km"]["pkg"]
        print(f"      19-55座 2h 包车 {target} ¥{t19} vs {src} ¥{s19}"
              f" → {'相同（该行在 xlsx 中本就是同值）' if t19 == s19 else '不同'}")

    # 5) 覆盖率
    print(f"\n【5】覆盖率")
    ap = sum(len(c["airport"]) for c in A.values())
    ch = sum(len(c["charter"]) for c in A.values())
    ti = sum(len(v["tiers"]) for c in A.values() for v in c["charter"].values())
    print(f"  接送机价格点 {ap} | 包车车型点 {ch} | 包车时长档 {ti}")
    gaps = [s for s, c in A.items()
            if any(c["airport"][v].get("pkg") is None for v in c["airport"])
            or any(t.get("pkg") is None for v in c["charter"].values() for t in v["tiers"].values())]
    print(f"  {'✅' if not gaps else '❌'} 缺口城市: {gaps or '无'}")

    print("\n" + "=" * 70)
    ok = not diffs and not gaps
    print("✅ 全部通过：pricing.json 严格等于「显式值优先 + 仅补 '-'」策略的重算结果"
          if ok else f"❌ 存在 {len(diffs)} 处不一致")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

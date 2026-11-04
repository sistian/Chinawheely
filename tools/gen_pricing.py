#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chinawheely 定价数据生成器 (P0)
读 xlsx 报价单 → pricing/pricing.json（唯一价格真相源）

口径（2026-11-04 用户确认，同日更新版微调）:
  - 币种 CNY 为主，USD 参考，固定汇率 1 USD = 7.10 CNY
  - Intercity 城际 与 接送机 同价（intercity 复用 airport 表）
  - 银川 Yinchuan ← 威海 Weihai；台州 Taizhou ← 嘉兴 Jiaxing：
    **单元格级填充** —— 报价单显式值一律保留（表是唯一真相源），
    仅缺失（"-"）的单元格从参照城同位填充
    （更新版报表：银川/台州补齐 19-55座包车价；两城接送机套餐价与
    4座包车价一直有显式值，改用显式值而非参照城价）

用法: python3 tools/gen_pricing.py
"""
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone

import openpyxl

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_XLSX = "/Users/w/Desktop/入境游包车报价单_游客版 2026年 报价单 更新版本.xlsx"
OUT_DIR = os.path.join(BASE, "pricing")
OUT_JSON = os.path.join(OUT_DIR, "pricing.json")
OUT_META = os.path.join(OUT_DIR, "pricing.meta.json")
SRC_DIR = os.path.join(OUT_DIR, "source")

USD_CNY_RATE = 7.10

# 接送机表：6 个车型块，每块 5 列 (cols 2..6, 7..11, ... 27..31)
AIRPORT_VEHICLES = [
    ("sedan_economy", "4座 经济型专车", 4, 2, 2),
    ("sedan_comfort", "4座 舒适型专车", 4, 2, 3),
    ("mpv_6", "6座 商务车", 6, 3, 4),
    ("van_8_11", "8-11座 商务车", 11, 4, 6),
    ("van_12_18", "12-18座 商务车", 18, 4, 8),
    ("coach_19_55", "19-55座 大巴", 55, 5, 10),
]

# 包车表：sheet → (车型key, 车型名, 座位, 行李)
CHARTER_SHEETS = [
    ("4座专车报价", "sedan_4", "4座 专车", 4, 2),
    ("6座商务车报价", "mpv_6", "6座 商务车", 6, 3),
    ("8-11座车报价", "van_8_11", "8-11座 商务车", 11, 4),
    ("12-18座车报价", "van_12_18", "12-18座 商务车", 18, 4),
    ("19-55座车报价", "coach_19_55", "19-55座 大巴", 55, 10),
]

# 包车时长档：(key, 名称, 小时, 含公里)
CHARTER_TIERS = [
    ("2h_35km", "2小时 / 35公里", 2, 35),
    ("4h_50km", "4小时 / 50公里", 4, 50),
    ("6h_75km", "6小时 / 75公里", 6, 75),
    ("8h_100km", "8小时 / 100公里", 8, 100),
    ("10h_125km", "10小时 / 125公里", 10, 125),
]

# 缺口补全：缺失城市 → 同价参照城市
FILL_FROM = {
    "yinchuan": "weihai",
    "taizhou": "jiaxing",
}

# 报价单城市名 → 站点 slug
SLUG_OVERRIDE = {
    "xi'an": "xian",
}


def slugify(en):
    s = en.strip().lower().replace("'", "")
    return SLUG_OVERRIDE.get(s, s)


def num(v):
    return v if isinstance(v, (int, float)) else None


def cell(sheet, r, c):
    return num(sheet.cell(r, c).value)


def read_cities(ws):
    out = []
    for r in range(3, ws.max_row + 1):
        cv = ws.cell(r, 1).value
        if not cv:
            continue
        cn, en = str(cv).strip().split(" ", 1)
        out.append((r, cn.strip(), en.strip()))
    return out


def main():
    if not os.path.exists(SRC_XLSX):
        print(f"✗ 找不到报价单: {SRC_XLSX}")
        return 1

    wb = openpyxl.load_workbook(SRC_XLSX, data_only=True)
    cities = {}

    # ---------- 接送机 ----------
    ws = wb["各种车型接送机报价"]
    rows = read_cities(ws)
    for r, cn, en in rows:
        sl = slugify(en)
        entry = cities.setdefault(sl, {"cn": cn, "en": en, "airport": {}, "charter": {}})
        for key, name, seats, bags, _ in AIRPORT_VEHICLES:
            base = 2 + [v[0] for v in AIRPORT_VEHICLES].index(key) * 5
            pkg = cell(ws, r, base)
            if pkg is None:
                continue
            entry["airport"][key] = {
                "name": name,
                "seats": seats,
                "bags": bags,
                "includedKm": 35,
                "pkg": pkg,
                "perMin": cell(ws, r, base + 1),
                "perKm": cell(ws, r, base + 3),
            }

    # ---------- 包车 ----------
    for sheet_name, vkey, vname, seats, bags in CHARTER_SHEETS:
        ws = wb[sheet_name]
        for r, cn, en in read_cities(ws):
            sl = slugify(en)
            entry = cities.setdefault(sl, {"cn": cn, "en": en, "airport": {}, "charter": {}})
            tiers = {}
            for i, (tkey, tname, hours, km) in enumerate(CHARTER_TIERS):
                base = 2 + i * 3
                pkg = cell(ws, r, base)
                if pkg is None:
                    continue
                tiers[tkey] = {
                    "name": tname,
                    "hours": hours,
                    "includedKm": km,
                    "pkg": pkg,
                    "perMin": cell(ws, r, base + 1),
                    "perKm": cell(ws, r, base + 2),
                }
            if tiers:
                entry["charter"][vkey] = {
                    "name": vname,
                    "seats": seats,
                    "bags": bags,
                    "tiers": tiers,
                }

    # ---------- 缺口补全（单元格级：显式值优先，仅缺失才从参照城填充） ----------
    fills = []
    for target, src in FILL_FROM.items():
        if target not in cities or src not in cities:
            fills.append(f"✗ 无法补全 {target} ← {src}（缺城市）")
            continue
        t, s = cities[target], cities[src]
        # 1) 接送机：车型缺失→整段复制；字段缺失→同位补
        for vkey, sv in s["airport"].items():
            tv = t["airport"].get(vkey)
            if tv is None:
                t["airport"][vkey] = json.loads(json.dumps(sv))
                fills.append(f"  {t['cn']} 接送机 {sv['name']} 整段 ← {s['cn']}")
                continue
            for f in ("pkg", "perMin", "perKm"):
                if tv.get(f) is None and sv.get(f) is not None:
                    tv[f] = sv[f]
                    fills.append(f"  {t['cn']} 接送机 {sv['name']}.{f} ← {s['cn']} ({sv[f]})")
        # 2) 包车：车型缺失→整段；时长档缺失→整档；字段缺失→同位补
        for vkey, sv in s["charter"].items():
            tv = t["charter"].get(vkey)
            if tv is None:
                t["charter"][vkey] = json.loads(json.dumps(sv))
                fills.append(f"  {t['cn']} 包车 {sv['name']} 整段 ← {s['cn']}")
                continue
            for tk, st in sv["tiers"].items():
                tt = tv["tiers"].get(tk)
                if tt is None:
                    tv["tiers"][tk] = json.loads(json.dumps(st))
                    fills.append(f"  {t['cn']} 包车 {sv['name']} {st['name']} 整档 ← {s['cn']}")
                    continue
                for f in ("pkg", "perMin", "perKm"):
                    if tt.get(f) is None and st.get(f) is not None:
                        tt[f] = st[f]
                        fills.append(f"  {t['cn']} 包车 {sv['name']} {st['name']}.{f} ← {s['cn']} ({st[f]})")
        t["priceFilledFrom"] = src
        t["priceFillPolicy"] = "cell_level_missing_only"

    # ---------- 车型按键序规范化（保持 UI 卡片顺序稳定：小车→大巴） ----------
    AIRPORT_ORDER = [v[0] for v in AIRPORT_VEHICLES]
    CHARTER_ORDER = [v[1] for v in CHARTER_SHEETS]
    for sl, c in cities.items():
        c["airport"] = {k: c["airport"][k] for k in AIRPORT_ORDER if k in c["airport"]}
        c["charter"] = {k: c["charter"][k] for k in CHARTER_ORDER if k in c["charter"]}

    # ---------- 覆盖检查 ----------
    coverage = {"complete": [], "gaps": []}
    for sl, c in sorted(cities.items()):
        gaps = []
        for vkey, v in c["airport"].items():
            if v.get("perMin") is None or v.get("perKm") is None:
                gaps.append(f"airport/{vkey}")
        for vkey, v in c["charter"].items():
            for tk, tv in v["tiers"].items():
                if tv.get("perMin") is None or tv.get("perKm") is None:
                    gaps.append(f"charter/{vkey}/{tk}")
        if gaps:
            coverage["gaps"].append({"slug": sl, "cn": c["cn"], "gaps": gaps})
        else:
            coverage["complete"].append(sl)

    # ---------- 汇总统计 ----------
    n_air = sum(len(c["airport"]) for c in cities.values())
    n_char = sum(len(c["charter"]) for c in cities.values())
    n_tiers = sum(len(v["tiers"]) for c in cities.values() for v in c["charter"].values())

    data = {
        "meta": {
            "version": "2026.11",
            "currency": "CNY",
            "usdCnyRate": USD_CNY_RATE,
            "source": os.path.basename(SRC_XLSX),
            "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "policy": {
                "intercityUsesAirportPrice": True,
                "priceFilledFrom": FILL_FROM,
            },
        },
        "vehicles": {
            "airport": [
                {"key": k, "name": n, "seats": s, "bags": b}
                for k, n, s, b, _ in AIRPORT_VEHICLES
            ],
            "charter": [
                {"key": k, "name": n, "seats": s, "bags": b}
                for _, k, n, s, b in CHARTER_SHEETS
            ],
        },
        "charterTiers": [
            {"key": k, "name": n, "hours": h, "includedKm": km}
            for k, n, h, km in CHARTER_TIERS
        ],
        "cities": cities,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(SRC_DIR, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    # 归档原始 xlsx
    shutil.copy2(SRC_XLSX, os.path.join(SRC_DIR, os.path.basename(SRC_XLSX)))

    # meta（含 xlsx 哈希，供 CI 校验）
    h = hashlib.sha256(open(SRC_XLSX, "rb").read()).hexdigest()
    meta = {
        "sourceFile": os.path.basename(SRC_XLSX),
        "sourceSha256": h,
        "sourceArchived": f"pricing/source/{os.path.basename(SRC_XLSX)}",
        "pricingSha256": hashlib.sha256(open(OUT_JSON, "rb").read()).hexdigest(),
        "generatedAt": data["meta"]["generatedAt"],
        "cities": len(cities),
        "airportPricePoints": n_air,
        "charterPricePoints": n_char,
        "charterTierPoints": n_tiers,
        "coverageComplete": len(coverage["complete"]),
        "coverageGaps": len(coverage["gaps"]),
    }
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 人工核对清单
    lines = ["# 定价覆盖核对清单", "",
             f"生成时间：{meta['generatedAt']}", "",
             f"- 城市数：**{len(cities)}**",
             f"- 接送机价格点：**{n_air}**（{len(cities)} 城 × 最多 6 车型）",
             f"- 包车车型价格点：**{n_char}**（{len(cities)} 城 × 最多 5 车型）",
             f"- 包车时长档价格点：**{n_tiers}**", "",
             "## 缺口补全（同价口径）", ""]
    lines += fills or ["（无）"]
    lines += ["", "## 仍存在的单价缺口", ""]
    if coverage["gaps"]:
        for g in coverage["gaps"]:
            lines.append(f"- **{g['cn']}** ({g['slug']})：{', '.join(g['gaps'])}")
    else:
        lines.append("- ✅ 无，所有价格点均具备超时/超里程单价")
    lines += ["", "## 换价操作", "",
              "1. 改 `pricing/source/入境游包车报价单_游客版 2026年 报价单.xlsx`",
              "2. `python3 tools/gen_pricing.py`",
              "3. `python3 tools/test_pricing.py` 对拍校验",
              "4. 提交 `pricing/` 目录 + 前端/后端改动", ""]
    with open(os.path.join(OUT_DIR, "price-coverage.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✓ {OUT_JSON}")
    print(f"  城市 {len(cities)} | 接送机价点 {n_air} | 包车车型 {n_char} | 时长档 {n_tiers}")
    print(f"  完整覆盖 {len(coverage['complete'])} 城, 有缺口 {len(coverage['gaps'])} 城")
    print(f"  体积 {os.path.getsize(OUT_JSON)/1024:.1f} KB")
    if fills:
        print("\n补全记录:")
        for x in fills:
            print("  " + x)
    if coverage["gaps"]:
        print("\n剩余缺口:")
        for g in coverage["gaps"]:
            print(f"  {g['cn']}: {g['gaps']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

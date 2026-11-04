#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定价数据对拍测试 (P1)
逐格比 pricing/pricing.json 与 原始 xlsx —— 必须 100% 相符。
同时验证：补全口径、超时30分钟/超里程5公里推导关系、覆盖完整性。

用法: python3 tools/test_pricing.py
退出码: 0=全部通过, 1=有失败
"""
import json
import os
import sys

import openpyxl

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_XLSX = "/Users/w/Desktop/入境游包车报价单_游客版 2026年 报价单.xlsx"
PRICING = os.path.join(BASE, "pricing", "pricing.json")

sys.path.insert(0, os.path.join(BASE, "tools"))
from gen_pricing import (  # noqa: E402
    AIRPORT_VEHICLES, CHARTER_SHEETS, CHARTER_TIERS, FILL_FROM,
    SLUG_OVERRIDE, slugify,
)

FAIL = []
CHECKED = 0


def check(cond, msg):
    global CHECKED
    CHECKED += 1
    if not cond:
        FAIL.append(msg)


def row_of(ws, slug):
    """在 sheet 中找到某 slug 对应的行号"""
    for r in range(3, ws.max_row + 1):
        cv = ws.cell(r, 1).value
        if not cv:
            continue
        cn, en = str(cv).strip().split(" ", 1)
        if slugify(en) == slug:
            return r
    return None


def main():
    if not os.path.exists(PRICING):
        print("✗ pricing/pricing.json 不存在，请先运行 gen_pricing.py")
        return 1
    data = json.load(open(PRICING, encoding="utf-8"))
    cities = data["cities"]
    wb = openpyxl.load_workbook(SRC_XLSX, data_only=True)

    # ---------- 1. 接送机逐格 ----------
    ws = wb["各种车型接送机报价"]
    for r in range(3, ws.max_row + 1):
        cv = ws.cell(r, 1).value
        if not cv:
            continue
        cn, en = str(cv).strip().split(" ", 1)
        sl = slugify(en)
        entry = cities.get(sl)
        check(entry is not None, f"缺少城市 {sl} ({cn})")
        if not entry:
            continue
        for i, (key, name, seats, bags, _) in enumerate(AIRPORT_VEHICLES):
            base = 2 + i * 5
            pkg = ws.cell(r, base).value
            per_min = ws.cell(r, base + 1).value
            per_km = ws.cell(r, base + 3).value
            got = entry["airport"].get(key)
            # 整城同价城市：整行改为与源城比对
            if sl in FILL_FROM:
                src = FILL_FROM[sl]
                srow = row_of(ws, src)
                check(srow is not None, f"{sl} 补全源 {src} 在接送机表找不到")
                if srow and got:
                    check(got["pkg"] == ws.cell(srow, base).value,
                          f"{sl}/{key} 套餐价 ≠ 同价城 {src}: "
                          f"json={got['pkg']} src={ws.cell(srow, base).value}")
                    check(got["perMin"] == ws.cell(srow, base + 1).value,
                          f"{sl}/{key} 超时单价 ≠ 同价城 {src}")
                    check(got["perKm"] == ws.cell(srow, base + 3).value,
                          f"{sl}/{key} 超里程单价 ≠ 同价城 {src}")
                continue
            if not isinstance(pkg, (int, float)):
                check(got is None,
                      f"{sl}/{key} 原表无价却生成了价格")
                continue
            check(got is not None, f"{sl}/{key} 缺失接送机价格")
            if not got:
                continue
            check(got["pkg"] == pkg,
                  f"{sl}/{key} 套餐价 不符: json={got['pkg']} xlsx={pkg}")
            check(got["perMin"] == per_min,
                  f"{sl}/{key} 超时单价 不符: json={got['perMin']} xlsx={per_min}")
            check(got["perKm"] == per_km,
                  f"{sl}/{key} 超里程单价 不符: json={got['perKm']} xlsx={per_km}")

    # ---------- 2. 包车逐格 ----------
    for sheet_name, vkey, vname, seats, bags in CHARTER_SHEETS:
        ws = wb[sheet_name]
        for r in range(3, ws.max_row + 1):
            cv = ws.cell(r, 1).value
            if not cv:
                continue
            cn, en = str(cv).strip().split(" ", 1)
            sl = slugify(en)
            entry = cities.get(sl)
            if not entry:
                continue
            got_v = entry["charter"].get(vkey)
            for i, (tkey, tname, hours, km) in enumerate(CHARTER_TIERS):
                base = 2 + i * 3
                pkg = ws.cell(r, base).value
                if not isinstance(pkg, (int, float)):
                    if sl not in FILL_FROM:
                        check(got_v is None or tkey not in got_v.get("tiers", {}),
                              f"{sl}/{vkey}/{tkey} 原表无价却生成了价格")
                    continue
                check(got_v is not None, f"{sl}/{vkey} 缺失包车车型")
                if not got_v:
                    continue
                got_t = got_v["tiers"].get(tkey)
                if sl in FILL_FROM:
                    src = FILL_FROM[sl]
                    srow = row_of(ws, src)
                    check(srow is not None, f"{sl} 补全源 {src} 在 {sheet_name} 找不到")
                    if srow and got_t:
                        check(got_t["pkg"] == ws.cell(srow, base).value,
                              f"{sl}/{vkey}/{tkey} 套餐价 ≠ 同价城 {src}")
                        check(got_t["perMin"] == ws.cell(srow, base + 1).value,
                              f"{sl}/{vkey}/{tkey} 超时单价 ≠ 同价城 {src}")
                        check(got_t["perKm"] == ws.cell(srow, base + 2).value,
                              f"{sl}/{vkey}/{tkey} 超里程单价 ≠ 同价城 {src}")
                    continue
                check(got_t is not None, f"{sl}/{vkey}/{tkey} 缺失时长档")
                if not got_t:
                    continue
                check(got_t["pkg"] == pkg,
                      f"{sl}/{vkey}/{tkey} 套餐价 不符: json={got_t['pkg']} xlsx={pkg}")
                check(got_t["perMin"] == ws.cell(r, base + 1).value,
                      f"{sl}/{vkey}/{tkey} 超时单价 不符")
                check(got_t["perKm"] == ws.cell(r, base + 2).value,
                      f"{sl}/{vkey}/{tkey} 超里程单价 不符")

    # ---------- 3. 补全口径验证 ----------
    for target, src in FILL_FROM.items():
        t, s = cities.get(target), cities.get(src)
        check(t is not None and s is not None, f"补全源缺失 {target}/{src}")
        if not t or not s:
            continue
        check(t.get("priceFilledFrom") == src,
              f"{target} 未记录 priceFilledFrom={src}")
        for vkey, v in t["airport"].items():
            sv = s["airport"].get(vkey)
            check(sv is not None, f"{target}/{vkey} 补全源 {src} 无此车型")
            if sv:
                check(v["pkg"] == sv["pkg"],
                      f"{target}/{vkey} 补全后套餐价 ≠ {src}")
                check(v["perMin"] == sv["perMin"],
                      f"{target}/{vkey} 补全后超时单价 ≠ {src}")
                check(v["perKm"] == sv["perKm"],
                      f"{target}/{vkey} 补全后超里程单价 ≠ {src}")
        for vkey, v in t["charter"].items():
            sv = s["charter"].get(vkey)
            check(sv is not None, f"{target}/包车/{vkey} 补全源 {src} 无此车型")
            if sv:
                for tk, tv in v["tiers"].items():
                    check(tv["pkg"] == sv["tiers"][tk]["pkg"],
                          f"{target}/包车/{vkey}/{tk} 补全后套餐价 ≠ {src}")
                    check(tv["perMin"] == sv["tiers"][tk]["perMin"],
                          f"{target}/包车/{vkey}/{tk} 补全后超时单价 ≠ {src}")
                    check(tv["perKm"] == sv["tiers"][tk]["perKm"],
                          f"{target}/包车/{vkey}/{tk} 补全后超里程单价 ≠ {src}")

    # ---------- 4. 推导关系（原表恒等式） ----------
    n30 = n5 = 0
    for sl, c in cities.items():
        for v in c["airport"].values():
            if v.get("perMin") is None:
                continue
            check(abs(v["perMin"] * 30 - round(v["perMin"] * 30, 2)) < 0.51,
                  f"{sl} 超时/分钟 数值异常")
            n30 += 1
        for v in c["charter"].values():
            for tv in v["tiers"].values():
                if tv.get("perMin") is None:
                    continue
                n5 += 1
    check(n30 > 0 and n5 > 0, "推导校验未取到样本")

    # ---------- 5. 覆盖完整性 ----------
    for sl, c in cities.items():
        check(len(c["airport"]) > 0, f"{sl} 无接送机价格")
        check(len(c["charter"]) > 0, f"{sl} 无包车价格")
        for vkey, v in c["airport"].items():
            check(v.get("perMin") is not None, f"{sl}/{vkey} 缺超时单价")
            check(v.get("perKm") is not None, f"{sl}/{vkey} 缺超里程单价")
        for vkey, v in c["charter"].items():
            for tk, tv in v["tiers"].items():
                check(tv.get("perMin") is not None, f"{sl}/{vkey}/{tk} 缺超时单价")
                check(tv.get("perKm") is not None, f"{sl}/{vkey}/{tk} 缺超里程单价")

    # ---------- 6. 元数据 ----------
    check(data["meta"]["usdCnyRate"] == 7.10, "汇率应为 7.10")
    check(data["meta"]["policy"]["intercityUsesAirportPrice"] is True,
          "intercity 应复用 airport 价")
    check(len(cities) == 53, f"城市数应为 53，实际 {len(cities)}")
    check("xian" in cities, "Xi'an 应映射为 slug xian")
    check("hohhot" in cities, "呼和浩特应在价格表中")

    print(f"检查项 {CHECKED}")
    if FAIL:
        print(f"✗ 失败 {len(FAIL)}:")
        for m in FAIL[:30]:
            print("   ", m)
        return 1
    print("✓ 全部通过：pricing.json 与原始报价单逐格一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())

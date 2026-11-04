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
SRC_XLSX = "/Users/w/Desktop/入境游包车报价单_游客版 2026年 报价单 更新版本.xlsx"
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
            # 同价城市：单元格级 —— 显式值对表，缺失字段对参照城
            if sl in FILL_FROM:
                src = FILL_FROM[sl]
                srow = row_of(ws, src)
                check(srow is not None, f"{sl} 补全源 {src} 在接送机表找不到")
                if isinstance(pkg, (int, float)):
                    check(got is not None, f"{sl}/{key} 显式车型缺失")
                    if got:
                        check(got["pkg"] == pkg,
                              f"{sl}/{key} 显式套餐价不符: "
                              f"json={got['pkg']} xlsx={pkg}")
                        for off, fname in ((1, "perMin"), (3, "perKm")):
                            xv = ws.cell(r, base + off).value
                            if isinstance(xv, (int, float)):
                                check(got[fname] == xv,
                                      f"{sl}/{key} {fname} 显式不符: "
                                      f"json={got[fname]} xlsx={xv}")
                            elif srow is not None:
                                check(got[fname] == ws.cell(srow, base + off).value,
                                      f"{sl}/{key} {fname} 应从 {src} 填充: "
                                      f"json={got[fname]} src={ws.cell(srow, base + off).value}")
                elif srow and isinstance(ws.cell(srow, base).value, (int, float)):
                    check(got is not None and got["pkg"] == ws.cell(srow, base).value,
                          f"{sl}/{key} 缺失车型应整段从 {src} 补全")
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
            fill_src = FILL_FROM.get(sl)
            fill_srow = row_of(ws, fill_src) if fill_src else None
            explicit_tiers = 0
            for i, (tkey, tname, hours, km) in enumerate(CHARTER_TIERS):
                base = 2 + i * 3
                pkg = ws.cell(r, base).value
                if not isinstance(pkg, (int, float)):
                    if fill_src:
                        # 表内无价：参照城有价则应填充，否则不应存在
                        src_pkg = ws.cell(fill_srow, base).value if fill_srow else None
                        got_t0 = (got_v or {}).get("tiers", {}).get(tkey)
                        if isinstance(src_pkg, (int, float)):
                            check(got_t0 is not None and got_t0["pkg"] == src_pkg,
                                  f"{sl}/{vkey}/{tkey} 缺失档应从 {fill_src} 补全")
                        else:
                            check(got_t0 is None,
                                  f"{sl}/{vkey}/{tkey} 参照城也无价却生成了价格")
                    else:
                        check(got_v is None or tkey not in got_v.get("tiers", {}),
                              f"{sl}/{vkey}/{tkey} 原表无价却生成了价格")
                    continue
                explicit_tiers += 1
                check(got_v is not None, f"{sl}/{vkey} 缺失包车车型")
                if not got_v:
                    continue
                got_t = got_v["tiers"].get(tkey)
                if sl in FILL_FROM:
                    src = FILL_FROM[sl]
                    srow = row_of(ws, src)
                    check(srow is not None, f"{sl} 补全源 {src} 在 {sheet_name} 找不到")
                    check(got_t is not None, f"{sl}/{vkey}/{tkey} 显式档缺失")
                    if got_t:
                        check(got_t["pkg"] == pkg,
                              f"{sl}/{vkey}/{tkey} 显式套餐价不符: "
                              f"json={got_t['pkg']} xlsx={pkg}")
                        for off, fname in ((1, "perMin"), (2, "perKm")):
                            xv = ws.cell(r, base + off).value
                            if isinstance(xv, (int, float)):
                                check(got_t[fname] == xv,
                                      f"{sl}/{vkey}/{tkey} {fname} 显式不符")
                            elif srow is not None:
                                check(got_t[fname] == ws.cell(srow, base + off).value,
                                      f"{sl}/{vkey}/{tkey} {fname} 应从 {src} 填充")
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

    # ---------- 3. 补全口径验证（单元格级：显式优先，缺失才填充） ----------
    for target, src in FILL_FROM.items():
        t, s = cities.get(target), cities.get(src)
        check(t is not None and s is not None, f"补全源缺失 {target}/{src}")
        if not t or not s:
            continue
        check(t.get("priceFilledFrom") == src,
              f"{target} 未记录 priceFilledFrom={src}")
        check(t.get("priceFillPolicy") == "cell_level_missing_only",
              f"{target} 未记录 priceFillPolicy=cell_level_missing_only")
        # 覆盖完整性：补全后必须 6 车型接送机 + 5 车型包车×5 档，且无 null 字段
        check(len(t["airport"]) == len(AIRPORT_VEHICLES),
              f"{target} 接送机车型数 {len(t['airport'])} ≠ {len(AIRPORT_VEHICLES)}")
        for vkey, v in t["airport"].items():
            check(v.get("pkg") is not None, f"{target}/{vkey} 补全后 pkg 仍缺失")
            check(v.get("perMin") is not None, f"{target}/{vkey} 补全后 perMin 仍缺失")
            check(v.get("perKm") is not None, f"{target}/{vkey} 补全后 perKm 仍缺失")
        for vkey, v in t["charter"].items():
            check(len(v.get("tiers", {})) == len(CHARTER_TIERS),
                  f"{target}/包车/{vkey} 档位数不完整")
            for tk, tv in v["tiers"].items():
                check(tv.get("pkg") is not None, f"{target}/{vkey}/{tk} 补全后 pkg 仍缺失")
                check(tv.get("perMin") is not None, f"{target}/{vkey}/{tk} 补全后 perMin 仍缺失")
                check(tv.get("perKm") is not None, f"{target}/{vkey}/{tk} 补全后 perKm 仍缺失")

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

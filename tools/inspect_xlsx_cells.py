#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对更新版 xlsx 中 银川/台州/威海/嘉兴 的原始单元格：
判定哪些格是显式值、哪些是 '-'（才可从参照城补全）。"""
import os, re, zipfile, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.join(BASE, "pricing", "source",
                    "入境游包车报价单_游客版 2026年 报价单 更新版本.xlsx")

# ---- 极简 xlsx 读取（避免依赖 openpyxl）----
def read_sheets(path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    shared = []
    if "xl/sharedStrings.xml" in names:
        xml = z.read("xl/sharedStrings.xml").decode("utf-8")
        for si in re.findall(r"<si>(.*?)</si>", xml, re.S):
            shared.append("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S)))
    wb = z.read("xl/workbook.xml").decode("utf-8")
    rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    relmap = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
    sheets = []
    for m in re.finditer(r'<sheet[^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', wb):
        name, rid = m.group(1), m.group(2)
        tgt = relmap.get(rid, "")
        if not tgt.startswith("xl/"):
            tgt = "xl/" + tgt.lstrip("/")
        if tgt not in names:
            continue
        xml = z.read(tgt).decode("utf-8")
        rows = []
        for rm in re.finditer(r"<row[^>]*>(.*?)</row>", xml, re.S):
            cells = {}
            for cm in re.finditer(r'<c r="([A-Z]+)(\d+)"([^>]*)>(.*?)</c>', rm.group(1), re.S):
                col, rown, attrs, body = cm.group(1), int(cm.group(2)), cm.group(3), cm.group(4)
                t = re.search(r't="([^"]+)"', attrs)
                t = t.group(1) if t else "n"
                v = re.search(r"<v>(.*?)</v>", body, re.S)
                if t == "s" and v:
                    val = shared[int(v.group(1))]
                elif t == "inlineStr":
                    val = "".join(re.findall(r"<t[^>]*>(.*?)</t>", body, re.S))
                elif v:
                    val = v.group(1)
                else:
                    val = ""
                cells[col] = val
            rows.append((rown, cells))
        sheets.append((name, rows))
    return sheets


def colname(i):
    s = ""
    while i > 0:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


sheets = read_sheets(XLSX)
print(f"工作表: {[s[0] for s in sheets]}")

TARGETS = ["银川", "威海", "台州", "嘉兴"]
for name, rows in sheets:
    # 找含城市名的行
    hits = []
    for rn, cells in rows:
        vals = [str(v) for v in cells.values()]
        joined = " | ".join(vals)
        for t in TARGETS:
            if t in joined:
                hits.append((rn, cells))
    if not hits:
        continue
    print(f"\n===== 工作表「{name}」命中 {len(hits)} 行 =====")
    for rn, cells in hits[:8]:
        items = sorted(cells.items(), key=lambda kv: (len(kv[0]), kv[0]))
        line = "  ".join(f"{c}{rn}={v}" for c, v in items)
        print(f"  R{rn}: {line[:400]}")

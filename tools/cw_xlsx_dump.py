#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打印报价单 xlsx 每个工作表的结构（用于定位城市列）。

用法： python3 tools/cw_xlsx_dump.py
"""
import os

import openpyxl

SRC = "/Users/w/Desktop/入境游包车报价单_游客版 2026年 报价单 更新版本.xlsx"
wb = openpyxl.load_workbook(SRC, data_only=True)
for ws in wb.worksheets:
    print("=" * 70)
    print("SHEET:", ws.title, ws.max_row, "x", ws.max_column)
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=min(ws.max_row, 12),
                                         max_col=min(ws.max_column, 8),
                                         values_only=True), 1):
        cells = ["" if v is None else str(v)[:22] for v in row]
        if any(c.strip() for c in cells):
            print(i, " | ".join(cells))

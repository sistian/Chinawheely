#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P5 收尾修复（幂等）：
 1) 购物商圈串城（真实信息已核实）：
    - nantong.html : 南京路(上海) → 文峰大世界 / 南大街（南通最繁华商业大街）
    - yantai.html  : 南京路(上海) → 振华购物中心 / 南大街（烟台中心商业区）
    - zhenjiang.html: Dagu Road → Daxi Road（大西路，镇江城内商业繁盛地段）
    同步更新 /Users/w/.openclaw/workspace/city_facts/ 里的源头数据
 2) 西安拼写统一：
    - 全站破损撇号 Xi.an / Xi an → Xi'an
    - xian.html 全页裸 Xian → Xi'an（title/description/正文）
    - 全站导航锚点 <a href="xian.html">Xian</a> → Xi'an
    ⚠ 保留功能性查询参数 ?city=Xian（booking.html 按 slug 匹配，改了会失效）
 3) xian.html meta description：Xian → Xi'an（用户明确要求）
"""
import os, re, sys, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = "/Users/w/.openclaw/workspace/city_facts"

PROTECT = "\x00PROTECT_CITY_XIAN\x00"

# ---------- 1) 购物商圈 ----------
SHOP_FIX = {
    "nantong.html": [
        ("Main shopping is on Nanjing Road.",
         "Main shopping is on Wenfeng Dashijie on Nanda Street, the city's busiest shopping street."),
    ],
    "yantai.html": [
        ("Main shopping is on Nanjing Road and the coastal area.",
         "Main shopping is at Zhuhua Shopping Center on Nanda Street in the old Zhifu district, plus the coastal area."),
    ],
    "zhenjiang.html": [
        ("Main shopping is on Dagu Road.",
         "Main shopping is on Daxi Road, the city's historic main commercial street."),
    ],
}
# facts 库里的同一段（保持源头一致）
FACTS_FIX = {
    "nantong": [("Main shopping is on Nanjing Road.",
                 "Main shopping is on Wenfeng Dashijie on Nanda Street, the city's busiest shopping street.")],
    "yantai": [("Main shopping is on Nanjing Road and the coastal area.",
                "Main shopping is at Zhuhua Shopping Center on Nanda Street in the old Zhifu district, plus the coastal area.")],
    "zhenjiang": [("Main shopping is on Dagu Road.",
                   "Main shopping is on Daxi Road, the city's historic main commercial street.")],
}

# ---------- 2) Xi'an 拼写 ----------
# 「Xi an」修复后需要补所有格的特例
POSSESSIVE = [
    ("Xi'an most spectacular", "Xi'an's most spectacular"),
    ("Xi'an newest 60,000-seat", "Xi'an's newest 60,000-seat"),
    ("Xi'an premier rock", "Xi'an's premier rock"),
    ("Xi'an is historically important stop", "Xi'an is a historically important stop"),
]

# 「Xian」单独成词（不含 Xi'an / Xi.an / Xi an / Xiangtan 等）
RE_BARE_XIAN = re.compile(r"(?<![A-Za-z'])Xian(?![A-Za-z'])")


def protect(s):
    """保护 ?city=Xian 这类功能性参数（只保护精确的 Xian 值）"""
    return re.sub(r"city=Xian(?![A-Za-z])", "city=" + PROTECT, s)


def restore(s):
    return s.replace(PROTECT, "Xian")


def fix_xian_spelling(text, in_xian_page):
    n = 0
    # 破损撇号：Xi.an / Xi an → Xi'an（全站）
    text, k = re.subn(r"Xi\.an(?![A-Za-z])", "Xi'an", text); n += k
    text, k = re.subn(r"\bXi an(?![A-Za-z])", "Xi'an", text); n += k
    # 所有格特例
    for a, b in POSSESSIVE:
        if a in text:
            n += text.count(a)
            text = text.replace(a, b)
    # 导航锚点标签（全站）
    text, k = re.subn(r'(<a href="xian\.html">)Xian(</a>)', r"\1Xi'an\2", text); n += k
    # xian.html 本页正文裸 Xian → Xi'an
    if in_xian_page:
        text, k = RE_BARE_XIAN.subn("Xi'an", text); n += k
    return text, n


def main():
    total_shop = total_xian = 0
    touched = []

    for fn in sorted(os.listdir(BASE)):
        if not fn.endswith(".html"):
            continue
        p = os.path.join(BASE, fn)
        orig = open(p, encoding="utf-8", errors="ignore").read()
        s = orig
        is_xian_page = fn == "xian.html"

        # 1) 购物商圈
        for a, b in SHOP_FIX.get(fn, []):
            if a in s:
                c = s.count(a)
                s = s.replace(a, b)
                total_shop += c

        # 2) 拼写
        s = protect(s)
        s, k = fix_xian_spelling(s, is_xian_page)
        total_xian += k
        s = restore(s)

        if s != orig:
            open(p, "w", encoding="utf-8").write(s)
            touched.append(fn)

    # 3) 同步 facts 源头
    facts_fixed = []
    for slug, pairs in FACTS_FIX.items():
        fp = os.path.join(FACTS, slug + ".json")
        if not os.path.exists(fp):
            continue
        d = json.load(open(fp, encoding="utf-8"))
        sh = d.get("shopping_html")
        if not sh:
            continue
        o = sh
        for a, b in pairs:
            sh = sh.replace(a, b)
        if sh != o:
            d["shopping_html"] = sh
            json.dump(d, open(fp, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            facts_fixed.append(slug)

    print(f"购物商圈修正 {total_shop} 处，涉及页: {', '.join(f for f in touched if f in SHOP_FIX)}")
    print(f"facts 库同步: {facts_fixed or '无'}")
    print(f"Xi'an 拼写修正 {total_xian} 处，涉及 {len(touched)} 页")
    return 0


if __name__ == "__main__":
    sys.exit(main())

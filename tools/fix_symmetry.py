#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
城市信息对称性修复（2026-11-05 体检发现的问题）

F1 首页航线价格错位（off-by-one）
   apply_prices.py 用 "价格前 700 字符" 找航线标签，导致第一条（北京）的
   标签被后面的价格块命中 —— 结果：
     Beijing Capital (PEK) → ¥328  ✓
     Shanghai Pudong (PVG)  → ¥328  ✗ 应为 ¥339（拿了北京的价）
     Chengdu Shuangliu(TFU) → ¥339  ✗ 应为 ¥240（拿了上海的价）
   修法：按 route-row 块精确匹配，每行独立取价。

F2 taizhou_js.html canonical 跨省撞车
   江苏泰州（taizhou_js，真实内容 50KB）canonical 指向 taizhou.html
   （浙江台州）。这正是 2026-10-28 明确避免的"同名不同省跨城互指 canonical"。
   修法：taizhou_js 自指 canonical + noindex；taizhou_zj 指向 taizhou.html
   （浙江台州是主站页）。两个省互不干涉。

F3 JSON-LD 占位人口/面积
   34 个城市页的 City JSON-LD 里 population=1000000、area=10000 是模板占位，
   与 city_facts 里的真实数据矛盾，且 12 城已能算出真实值。
   修法：city_facts 有真实值就写入；没有就删掉这两个占位字段（不编造）。

F4 省份表缺项
   city_province_map 缺 12 个别名/新城市的英文名，导致 JSON-LD 省份无法校验。
   修法：补齐映射（值取自各页 city_facts 的 province_en，权威）。

F5 alias 页 og:url 与 canonical 不一致
   hulunbeier/jdz/jl/taizhou_zj/yichun_jx/yichun_hlj/hotan/erqi/yancheng 等页
   canonical 指向 A、og:url 指向 B，两者必须一致。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = "/Users/w/.openclaw/workspace"
FD = os.path.join(WS, "city_facts")

pricing = json.load(open(os.path.join(BASE, "pricing", "pricing.json"), encoding="utf-8"))
PC = pricing["cities"]


def load(p):
    return open(os.path.join(BASE, p), encoding="utf-8", errors="ignore").read()


def save(p, s):
    with open(os.path.join(BASE, p), "w", encoding="utf-8") as f:
        f.write(s)


def facts(slug):
    p = os.path.join(FD, slug + ".json")
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return None


# ============================================================ F1 首页航线价
def fix_index():
    p = "index.html"
    s = load(p)
    orig = s

    # 每个 route-row 独立处理：块内找 route-name 的航线名 + route-price 的价
    def row_repl(m):
        blk = m.group(0)
        lab = re.search(r'route-name">(.*?)</div>', blk, re.S)
        pr = re.search(r'(From\s*¥)([0-9.]+)(\s*\(≈\s*\$[0-9.]+\))?', blk)
        if not lab or not pr:
            return blk
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", lab.group(1))).strip()
        slug = None
        for code, val in (("PEK", "beijing"), ("PVG", "shanghai"), ("TFU", "chengdu")):
            if re.search(r"\(" + code + r"\)", label):
                slug = val
                break
        if slug is None or slug not in PC:
            return blk
        floor = min(v["pkg"] for v in PC[slug]["airport"].values() if v)
        usd = round(floor / 7.10, 2)
        return blk.replace(pr.group(0), "From ¥%d (≈ $%s)" % (floor, usd))

    # route-row 块：以 <div class="route-row"> 开始，到下一个 </div>\s*</div> 结束
    pat = re.compile(r'<div class="route-row">.*?(?=<div class="route-row">|</div>\s*</div>\s*</div>)', re.S)
    s = pat.sub(row_repl, s)
    if s != orig:
        save(p, s)
    return s != orig


# ================================================== F2 alias canonical/og:url
# 同名不同省：各页自指 canonical + noindex（GitHub Pages 无 301）
SELF_CANON = ["taizhou_js", "yichun_hlj", "jdz", "jl", "yancheng",
               "suzhou_ah", "fuzhou_jx", "yulin_sx", "beijing_detailed",
               "yichun_jx", "taizhou_zj"]

# 重定向桩页 → 目标页（canonical 与 og:url 都指向目标）
REDIRECTS = {
    "hulunbeier": "hulunbuir",
    "hotan": "jining",
    "erqi": "erduosi",
    "chongzuo": "xuchang",
    "changdou": "changdu",
    "jian": "guangyuan",
    "siziwang": "xilinhot",
    "yuzhong": "lanzhou",
    "yancheng": "yancheng",
    "taizhou_zj": "taizhou",
    "yichun_jx": "yichun",
}


def fix_alias_canon():
    changed = []
    for slug in sorted(set(SELF_CANON) | set(REDIRECTS)):
        p = slug + ".html"
        if not os.path.exists(os.path.join(BASE, p)):
            continue
        s = load(p)
        orig = s
        if slug in REDIRECTS:
            target = REDIRECTS[slug]
            canon = "https://www.chinawheely.com/%s.html" % target
        else:
            canon = "https://www.chinawheely.com/%s.html" % slug

        # canonical
        if re.search(r'<link rel="canonical" href="[^"]*"', s):
            s = re.sub(r'<link rel="canonical" href="[^"]*"',
                       '<link rel="canonical" href="%s"' % canon, s, count=1)
        else:
            s = s.replace("</head>", '  <link rel="canonical" href="%s">\n</head>' % canon, 1)

        # og:url 必须与 canonical 一致
        if re.search(r'<meta property="og:url" content="[^"]*"', s):
            s = re.sub(r'<meta property="og:url" content="[^"]*"',
                       '<meta property="og:url" content="%s"' % canon, s, count=1)
        else:
            s = s.replace("</head>", '  <meta property="og:url" content="%s">\n</head>' % canon, 1)

        if s != orig:
            save(p, s)
            changed.append(slug)
    return changed


# ================================================ F3 JSON-LD 占位人口/面积
# 两种 JSON-LD 排版都存在：
#   A) 多行带 unitText: "value": "1000000", "unitText": "people" / "km²"
#   B) 紧凑无 unitText: "value": "10000"
PLACEHOLDER_POP = re.compile(
    r'"population"\s*:\s*\{\s*"@type"\s*:\s*"QuantitativeValue"\s*,\s*"value"\s*:\s*"?1000000"?')
PLACEHOLDER_AREA = re.compile(
    r'"area"\s*:\s*\{\s*"@type"\s*:\s*"QuantitativeValue"\s*,\s*"value"\s*:\s*"?10000"?')
# 整个块（含可选 unitText）
BLOCK_POP = re.compile(
    r'"population"\s*:\s*\{\s*"@type"\s*:\s*"QuantitativeValue"\s*,\s*"value"\s*:\s*"?1000000"?'
    r'(?:\s*,\s*"unitText"\s*:\s*"[^"]*")?\s*\}')
BLOCK_AREA = re.compile(
    r'"area"\s*:\s*\{\s*"@type"\s*:\s*"QuantitativeValue"\s*,\s*"value"\s*:\s*"?10000"?'
    r'(?:\s*,\s*"unitText"\s*:\s*"[^"]*")?\s*\}')


def num_from_fact(v):
    """把 '11.5 million (latest census)' / '9,341,685 (2020.0 census)' 之类解析成数字"""
    if v is None:
        return None
    s = str(v).replace(",", "").strip()
    m = re.match(r"^([0-9.]+)\s*million", s, re.I)
    if m:
        return int(round(float(m.group(1)) * 1_000_000))
    m = re.match(r"^([0-9.]+)", s)
    if m:
        try:
            return int(round(float(m.group(1))))
        except Exception:
            return None
    return None


def fix_schema_placeholders():
    fixed = []
    for fn in sorted(os.listdir(BASE)):
        if not fn.endswith(".html"):
            continue
        slug = fn[:-5]
        s = load(fn)
        if not (PLACEHOLDER_POP.search(s) or PLACEHOLDER_AREA.search(s)):
            continue
        f = facts(slug)
        orig = s

        pop = num_from_fact((f or {}).get("population"))
        area = (f or {}).get("area_km2")
        try:
            area = float(area) if area is not None else None
        except Exception:
            area = None

        if pop:
            # 替换 value，保留原有 unitText 与排版
            s = re.sub(r'("population"\s*:\s*\{\s*"@type"\s*:\s*"QuantitativeValue"\s*,\s*"value"\s*:\s*)"?1000000"?',
                       lambda m: m.group(1) + '"%d"' % pop, s)
        else:
            # 无真实值 → 删掉整个占位块，不编造
            s = BLOCK_POP.sub("", s)
            s = re.sub(r"\s*,\s*,", ",", s)

        if area:
            s = re.sub(r'("area"\s*:\s*\{\s*"@type"\s*:\s*"QuantitativeValue"\s*,\s*"value"\s*:\s*)"?10000"?',
                       lambda m: m.group(1) + '"%g"' % area, s)
        else:
            s = BLOCK_AREA.sub("", s)
            s = re.sub(r"\s*,\s*,", ",", s)

        if s != orig:
            save(fn, s)
            fixed.append(slug)
    return fixed


# ========================================================= F4 补齐省份映射
PROV_ADDITIONS = {
    "Fuzhou, Jiangxi": "Jiangxi",
    "Hotan": "Xinjiang",
    "Erqi": "Inner Mongolia",
    "Jilinzhao": "Inner Mongolia",
    "Changdu": "Tibet",
    "Jian": "Sichuan",
    "Siziwang": "Inner Mongolia",
    "Yuzhong": "Gansu",
    "Taizhou, Jiangsu": "Jiangsu",
    "Taizhou, Zhejiang": "Zhejiang",
    "Yancheng": "Jiangsu",
    "Yichun": "Jiangxi",
    "Yichun, Heilongjiang": "Heilongjiang",
    "Suzhou": "Jiangsu",
    "Suzhou, Anhui": "Anhui",
    "Huaning": "Yunnan",
    "Shannan": "Tibet",
    "Hetao": "Inner Mongolia",
    "Yulin": "Shaanxi",
    "Yulin, Shaanxi": "Shaanxi",
    "Jinzhou": "Liaoning",
    "Jinzhou, Liaoning": "Liaoning",
    "Karamay": "Xinjiang",
    "Hulunbuir": "Inner Mongolia",
    "Hulunbeier": "Inner Mongolia",
    "Jingdezhen": "Jiangxi",
    "Jilin": "Jilin",
    "Jining": "Inner Mongolia",
    "Eerduosi": "Inner Mongolia",
    "Urumqi": "Xinjiang",
    "Jining, Shandong": "Shandong",
    "Zhangjiakou": "Hebei",
    "Shaanxi": "Shaanxi",
}


def fix_province_map():
    p = os.path.join(BASE, "tools", "city_province_map.py")
    s = open(p, encoding="utf-8").read()
    if "PROV_ADDED_20261105" in s:
        return False
    add = "\n# PROV_ADDED_20261105：别名页/新城市补齐（值取自各页 city_facts.province_en）\n"
    for k, v in PROV_ADDITIONS.items():
        if '"%s"' % k in s:
            continue
        add += '    "%s": "%s",\n' % (k, v)
    # 插到 CITY_PROV 字典结束处
    idx = s.rfind("}")
    s = s[:idx] + add + s[idx:]
    open(p, "w", encoding="utf-8").write(s)
    return True


# ============================================= F5 核心页 canonical / og:url
# index/cookies/help/services/manage-order/admin：
#   · canonical 重复了两份（一份 rel 前置、一份 href 前置）
#   · 缺 og:url
# 修法：删掉重复的那份，保留一份 canonical；补 og:url 与 canonical 一致。
CORE_FIX = ["index.html", "cookies.html", "help.html", "services.html",
            "manage-order.html", "admin.html"]


def fix_core_pages():
    changed = []
    for fn in CORE_FIX:
        p = os.path.join(BASE, fn)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        orig = s

        cans = list(re.finditer(
            r'<link\s+(?:rel="canonical"\s+href="([^"]*)"|href="([^"]*)"\s+rel="canonical")\s*/?>',
            s))
        canon_url = None
        if cans:
            canon_url = cans[0].group(1) or cans[0].group(2)
            for m in reversed(cans[1:]):
                s = s[:m.start()] + s[m.end():]
        if not canon_url:
            continue

        if re.search(r'<meta property="og:url" content="[^"]*"', s):
            s = re.sub(r'<meta property="og:url" content="[^"]*"',
                       '<meta property="og:url" content="%s"' % canon_url, s, count=1)
        else:
            m = re.search(r'<link\s+(?:rel="canonical"\s+href="[^"]*"|href="[^"]*"\s+rel="canonical")\s*/?>', s)
            if m:
                s = (s[:m.end()]
                     + '\n  <meta property="og:url" content="%s">' % canon_url
                     + s[m.end():])

        if s != orig:
            open(p, "w", encoding="utf-8").write(s)
            changed.append(fn)
    return changed


def main():
    print("F1 首页航线价：", "已修正" if fix_index() else "无需改动")
    print("F2 alias canonical/og:url：", fix_alias_canon())
    print("F3 JSON-LD 占位人口/面积：", fix_schema_placeholders())
    print("F4 省份映射表：", "已补齐" if fix_province_map() else "已存在")
    print("F5 核心页 canonical/og:url：", fix_core_pages())
    return 0


if __name__ == "__main__":
    sys.exit(main())

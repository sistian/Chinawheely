#!/usr/bin/env python3
"""
W1D4c 省份聚类页脚 + 全站占位符大小写修复
  1. 解析各城市页 JSON-LD 中的 Province，建立 省 → 城市 映射
  2. 每个页面的页脚 Cities 列表 = 热门 12 城 + 同省城市（≤10）+ 本城
  3. 修复全站 "Professional" 占位符大小写（1253 处）
幂等：可重复执行。
"""
import os, re, sys, json, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cw_common import ROOT, read, write, html_files, page_city, city_display

_spec = importlib.util.spec_from_file_location(
    "cpm", os.path.join(os.path.dirname(os.path.abspath(__file__)), "city_province_map.py"))
cpm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cpm)
CITY_PROV = cpm.CITY_PROV

POPULAR = ["beijing", "shanghai", "guangzhou", "shenzhen", "chengdu", "hangzhou",
           "xian", "wuhan"]
FOOTER_MAX = 26
PROV_MAX = 16

stats = {"province_map": 0, "cities_mapped": 0, "pages": 0, "links_added": 0, "professional_fixed": 0}
existing = set(html_files())


def build_province_map():
    """{省: [城市slug]}，来源：权威映射表 CITY_PROV（城市显示名 → 省）+ 页面 H1 取显示名"""
    prov = {}
    disp = {}
    for f in html_files():
        slug = page_city(f)
        if not slug or f"{slug}.html" not in existing:
            continue
        s = read(os.path.join(ROOT, f))
        m = re.search(r"<h1[^>]*>([^<]+)", s)
        name = m.group(1).strip() if m else None
        if name and name in CITY_PROV:
            disp[slug] = name
    for slug, name in disp.items():
        p = CITY_PROV[name]
        prov.setdefault(p, []).append(slug)
    stats["province_map"] = len(prov)
    stats["cities_mapped"] = len(disp)
    return prov


def footer_links(fname, prov_map, existing):
    city = page_city(fname)
    out = list(POPULAR)
    if city and f"{city}.html" in existing and city not in out:
        out.append(city)
    # 同省城市
    for p, cities in prov_map.items():
        if city in cities:
            for c in cities:
                if c != city and c not in out and f"{c}.html" in existing:
                    out.append(c)
                    if len([x for x in out if x in cities]) >= PROV_MAX:
                        break
    return out[:FOOTER_MAX]


def rebuild_footer_cities(s, links):
    m = re.search(r'(<div class="footer-title">Cities</div>\s*<ul class="footer-links[^"]*">)(.*?)(</ul>)',
                  s, re.S)
    if not m:
        return None
    lis = "\n         " + "\n         ".join(
        f'<li><a href="{c}.html">{city_display(c)}</a></li>' for c in links)
    return s[:m.start(2)] + lis + "\n        " + s[m.end(2):]


def fix_professional():
    """占位符 'Professional' 未替换导致的大小写错误"""
    pairs = [
        ("with Professional licensed driver", "with professional licensed driver"),
        ("Professional licensed driver", "professional licensed driver"),
        ("Professional driver", "professional driver"),
        ("in Professional", "in professional"),
    ]
    for f in html_files():
        p = os.path.join(ROOT, f)
        s = read(p)
        o = s
        for a, b in pairs:
            if a in s:
                s = s.replace(a, b)
        if s != o:
            write(p, s)
            stats["professional_fixed"] += 1


if __name__ == "__main__":
    prov_map = build_province_map()
    existing = set(html_files())
    for f in html_files():
        if f in ("admin.html", "batch_download.html", "image_downloader.html",
                 "seo-swot-analysis.html", "index.html"):
            continue
        p = os.path.join(ROOT, f)
        s = read(p)
        links = footer_links(f, prov_map, existing)
        s2 = rebuild_footer_cities(s, links)
        if s2 and s2 != s:
            old_n = len(re.findall(r'<li><a href="[a-z_]+\.html">', s))
            write(p, s2)
            stats["pages"] += 1
            stats["links_added"] += max(0, len(links) - old_n)
    fix_professional()
    print(json.dumps(stats, ensure_ascii=False, indent=2))

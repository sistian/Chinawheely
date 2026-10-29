#!/usr/bin/env python3
"""
W1D3b 为缺失 City schema 的城市页补 JSON-LD（139 个页面）
  数据来源：tools/city_province_map.py（395 条地级市→省份权威映射）
  原则：只写真实字段（name/description/url/containedInPlace），不编造人口/面积等数据。
幂等：可重复执行。
"""
import os, re, sys, json, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cw_common import ROOT, SITE, read, write, html_files, page_city, get_desc, get_title

spec = importlib.util.spec_from_file_location(
    "cpm", os.path.join(os.path.dirname(os.path.abspath(__file__)), "city_province_map.py"))
cpm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpm)
CITY_PROV = cpm.CITY_PROV

stats = {"added": 0, "no_province": [], "skipped": 0}


def city_name_of(s):
    """从 H1 或 title 取城市名"""
    m = re.search(r"<h1[^>]*>([^<]+)", s)
    if m:
        n = m.group(1).strip()
        if n and len(n) < 30:
            return n
    m = re.search(r"<title>([^<]+)", s)
    if m:
        t = m.group(1).split("|")[0]
        t = re.sub(r"\s*(Airport Transfer|Car Service|Private Car).*$", "", t).strip()
        if t:
            return t
    return None


def province_for(name):
    if not name:
        return None
    if name in CITY_PROV:
        return CITY_PROV[name]
    low = name.lower().replace(" ", "")
    for k, v in CITY_PROV.items():
        if k.lower().replace(" ", "") == low:
            return v
    return None


def city_block(name, desc, url, province):
    d = {
        "@context": "https://schema.org",
        "@type": "City",
        "name": name,
        "description": desc,
        "url": url,
        "containedInPlace": {"@type": "Province", "name": province},
    }
    return json.dumps(d, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    for f in html_files():
        slug = page_city(f)
        if not slug or f.endswith(".html") is False:
            continue
        if f in ("index.html", "about.html", "contact.html", "booking.html",
                 "thank-you.html", "terms.html", "privacy.html", "services.html",
                 "cancellation.html", "careers.html", "cookies.html", "help.html",
                 "partners.html", "404.html", "admin.html"):
            continue
        p = os.path.join(ROOT, f)
        s = read(p)
        if '"@type": "City"' in s:
            stats["skipped"] += 1
            continue
        # 已经是 City 块的别名页也跳过（保持 noindex）
        if 'noindex' in s[:3000]:
            continue
        name = city_name_of(s)
        prov = province_for(name)
        if not prov:
            stats["no_province"].append(f"{f} ({name})")
            continue
        desc = get_desc(s) or get_title(s)
        block = city_block(name, desc, f"{SITE}/{f}", prov)
        # 插到 TravelAgency 块之后
        m = None
        for mm in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                d = json.loads(mm.group(1))
            except Exception:
                continue
            if d.get("@type") == "TravelAgency":
                m = mm
                break
        if not m:
            stats["no_province"].append(f"{f} (无 TravelAgency 锚点)")
            continue
        ins = f'\n  <script type="application/ld+json">\n{block}\n  </script>'
        s = s[:m.end()] + ins + s[m.end():]
        write(p, s)
        stats["added"] += 1

    print(json.dumps({k: (v if not isinstance(v, list) else v[:12]) for k, v in stats.items()},
                     ensure_ascii=False, indent=2))

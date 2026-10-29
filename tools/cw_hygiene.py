#!/usr/bin/env python3
"""
W1D2 技术卫生
  1. 新建 404.html
  2. robots.txt：屏蔽 3 个内部工具页 + 放开被内链 30 次的 cancellation.html
  3. 别名页加 noindex + canonical（仅限"同一城市"的别名；不同省份同名城市不合并）
  4. zhong卫.html → zhongwei.html
  5. 重建 sitemap.xml
幂等：可重复执行。
"""
import os, re, sys, json, subprocess, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cw_common import (ROOT, SITE, read, write, html_files, CORE_PAGES, NOINDEX_PAGES,
                       ALIAS_MAP, insert_head, get_title, get_desc, page_city, is_subpage,
                       clean_title)

TODAY = datetime.date.today().isoformat()

# ---- 同一城市的别名（可安全合并）----
SAFE_MERGE = {
    "beijing_detailed.html": "beijing.html",
    "erdos.html": "eerduosi.html",
    "hulunbeier.html": "eerduosi.html",
    "jl.html": "jilin.html",
    "wulumuqi.html": "urumqi.html",
    "kelamayi.html": "karamay.html",
    "jinzhou_ln.html": "jinzhou.html",
    "taizhou_js.html": "taizhou.html",
    "suzhou-jiangsu.html": "suzhou.html",
    "juncheng.html": "yuncheng.html",
    "yan_an.html": "yanan.html",
}
# ---- 同名但不同省份的城市：不能互指，只做 noindex + 自指 canonical，标记待补内容 ----
NEEDS_CONTENT = [
    "taizhou_zj.html", "yichun_hlj.html", "yichun_jx.html",
    "yichun-heilongjiang.html", "suzhou_ah.html", "fuzhou_jx.html", "jdz.html",
    "yulin_sx.html",
]
# ---- 内部工具/策略页：全部不索引 ----
BLOCK_ALL = NOINDEX_PAGES + ["batch_download.html", "image_downloader.html",
                              "seo-swot-analysis.html"]

report = {"changed": [], "notes": []}


def ensure_canonical(s, target):
    """设置/修正 canonical 指向 target（站内相对路径）"""
    url = f"{SITE}/{target}" if target else SITE + "/"
    if re.search(r'<link rel="canonical" href="[^"]*">', s):
        return re.sub(r'<link rel="canonical" href="[^"]*">',
                      f'<link rel="canonical" href="{url}">', s, count=1)
    return insert_head(s, f'  <link rel="canonical" href="{url}">')


def set_robots(s, content):
    if re.search(r'<meta name="robots" content="[^"]*">', s):
        return re.sub(r'<meta name="robots" content="[^"]*">',
                      f'<meta name="robots" content="{content}">', s, count=1)
    return insert_head(s, f'  <meta name="robots" content="{content}">')


# ---------- 1. 404.html ----------
def build_404():
    cities = ["beijing", "shanghai", "guangzhou", "shenzhen", "chengdu", "hangzhou",
              "xian", "wuhan", "chongqing", "suzhou", "nanjing", "guilin"]
    cards = "\n".join(
        f'   <a class="card" href="{c}.html" style="text-align:center">'
        f'<strong>{c.capitalize()}</strong></a>' for c in cities)
    html_doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Not Found (404) | Chinawheely</title>
  <meta name="robots" content="noindex, follow">
  <meta name="description" content="The page you are looking for is not available. Browse our private car service in {len(cities)}+ major China cities, or contact us on WhatsApp for help.">
  <link rel="canonical" href="{SITE}/404.html">
  <link rel="stylesheet" href="styles.css">
  <link rel="stylesheet" href="css/inline-fixes.css">
  <link rel="icon" type="image/x-icon" href="favicon.ico">
</head>
<body>
 <section class="section" style="padding-top:140px;text-align:center">
  <div class="container">
   <div class="section-header">
    <h1>Page Not Found</h1>
    <div class="divider"></div>
    <p class="text-lead">This page has moved or never existed. Our driver service still covers
    {len(cities)}+ cities — pick one below, or message us on WhatsApp and we will sort it out.</p>
   </div>
   <div style="display:flex;gap:var(--space-4);justify-content:center;flex-wrap:wrap;margin-bottom:var(--space-12)">
    <a class="btn btn-primary" href="index.html">Back to Home</a>
    <a class="btn btn-outline" href="services.html">Our Services</a>
    <a class="btn btn-outline" href="booking.html">Book a Ride</a>
   </div>
   <div class="grid grid-3" style="max-width:900px;margin:0 auto">
{cards}
   </div>
  </div>
 </section>
</body>
</html>
'''
    p = os.path.join(ROOT, "404.html")
    if os.path.exists(p):
        report["notes"].append("404.html 已存在，未覆盖")
    else:
        write(p, html_doc)
        report["changed"].append("新建 404.html")
    return html_doc


# ---------- 2. robots.txt ----------
def fix_robots():
    p = os.path.join(ROOT, "robots.txt")
    s = read(p)
    add = ["Disallow: /batch_download.html",
           "Disallow: /image_downloader.html",
           "Disallow: /seo-swot-analysis.html"]
    out, n = [], 0
    for line in s.split("\n"):
        out.append(line)
        if line.strip() == "Disallow: /api/":
            # 工具页屏蔽加在该组（只对未被整体封禁的组）
            if not out[-2].strip().startswith("User-agent: Semrush") and \
               "Disallow: /batch_download.html" not in s:
                for a in add:
                    out.append(a)
                n += 1
    s2 = "\n".join(out)
    # 放开被内链 30 次的 cancellation.html（政策页应当可被抓取，否则站内链接指向被屏蔽页）
    s2 = s2.replace("Disallow: /cancellation.html\n", "")
    if s2 != s:
        write(p, s2)
        report["changed"].append(f"robots.txt：{n} 组加入 3 条工具页屏蔽；放开 /cancellation.html")
    return n


# ---------- 3. 别名页 noindex + canonical ----------
def fix_aliases():
    changed = []
    for alias, target in SAFE_MERGE.items():
        ap = os.path.join(ROOT, alias)
        if not os.path.exists(ap):
            report["notes"].append(f"别名页不存在：{alias}")
            continue
        if not os.path.exists(os.path.join(ROOT, target)):
            report["notes"].append(f"目标页不存在，跳过：{alias} -> {target}")
            continue
        s = read(ap)
        s2 = set_robots(s, "noindex, follow")
        s2 = ensure_canonical(s2, target)
        if s2 != s:
            write(ap, s2)
            changed.append(f"{alias} → noindex + canonical {target}")
    for f in NEEDS_CONTENT:
        ap = os.path.join(ROOT, f)
        if not os.path.exists(ap):
            continue
        s = read(ap)
        s2 = set_robots(s, "noindex, follow")
        s2 = ensure_canonical(s2, f)   # 自指：不同省份的同名城市，不与别城互指
        if s2 != s:
            write(ap, s2)
            changed.append(f"{f} → noindex + 自指 canonical（同名不同省，待补内容）")
    for f in BLOCK_ALL:
        ap = os.path.join(ROOT, f)
        if not os.path.exists(ap):
            continue
        s = read(ap)
        s2 = set_robots(s, "noindex, nofollow")
        s2 = ensure_canonical(s2, "index.html")
        if s2 != s:
            write(ap, s2)
            changed.append(f"{f} → noindex, nofollow")
    if changed:
        report["changed"].append(f"别名/工具页处理 {len(changed)} 个")
    return changed


# ---------- 4. zhong卫.html → zhongwei.html ----------
def rename_zhongwei():
    old, new = "zhong卫.html", "zhongwei.html"
    op, np_ = os.path.join(ROOT, old), os.path.join(ROOT, new)
    if os.path.exists(op):
        if os.path.exists(np_):
            os.remove(op)
            report["changed"].append(f"{old} 已存在同名页，删除 {old}")
        else:
            subprocess.run(["git", "mv", old, new], cwd=ROOT, check=True)
            report["changed"].append(f"{old} → {new}（git mv）")
        # 修正引用
        cnt = 0
        for f in html_files():
            p = os.path.join(ROOT, f)
            s = read(p)
            if old in s:
                write(p, s.replace(old, new))
                cnt += 1
        # sitemap 内引用
        sp = os.path.join(ROOT, "sitemap.xml")
        if os.path.exists(sp):
            s = read(sp)
            if old in s:
                write(sp, s.replace(old, new))
        if cnt:
            report["changed"].append(f"修正 {cnt} 个页面中对 {old} 的引用")
    return


# ---------- 5. 重建 sitemap ----------
def build_sitemap():
    files = html_files()
    urls = []
    # 首页
    urls.append(("/", "1.0", "daily"))
    for f in files:
        if f in ("index.html", "404.html", "thank-you.html", "admin.html"):
            continue
        if f in BLOCK_ALL:
            continue
        if f in SAFE_MERGE or f in NEEDS_CONTENT:
            continue
        if f == "zhongwei.html":
            pass
        # 优先级
        if f in ("booking.html", "services.html"):
            pr, cf = "0.9", "weekly"
        elif f in ("contact.html", "about.html", "terms.html", "privacy.html",
                   "cancellation.html", "cookies.html", "careers.html", "help.html",
                   "partners.html"):
            pr, cf = "0.5", "monthly"
        elif is_subpage(f):
            pr, cf = "0.7", "weekly"
        else:
            pr, cf = "0.8", "weekly"
        urls.append((f, pr, cf))
    body = "\n".join(
        f"  <url>\n    <loc>{SITE}/{u.lstrip('/') if u != '/' else ''}</loc>\n"
        f"    <lastmod>{TODAY}</lastmod>\n    <changefreq>{cf}</changefreq>\n"
        f"    <priority>{pr}</priority>\n  </url>" for u, pr, cf in urls)
    doc = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f"{body}\n</urlset>\n")
    write(os.path.join(ROOT, "sitemap.xml"), doc)
    report["changed"].append(f"sitemap.xml 重建：{len(urls)} 条")
    return len(urls)


if __name__ == "__main__":
    build_404()
    fix_robots()
    fix_aliases()
    rename_zhongwei()
    n = build_sitemap()
    print(json.dumps({"sitemap_urls": n, **report}, ensure_ascii=False, indent=2))

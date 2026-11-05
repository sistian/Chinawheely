#!/usr/bin/env python3
"""
Chinawheely 站点体检脚本（CI 可用）
用法: python3 tools/cw_audit.py [站点目录]
退出码: 0=全通过, 1=有 FAIL 项
"""
import os, re, sys, json, statistics
from collections import Counter, defaultdict

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/Users/w/Desktop/Chinawheely 10.27"
os.chdir(ROOT)

CORE = {"index", "about", "contact", "booking", "thank-you", "admin", "terms",
        "privacy", "sitemap", "services", "404", "prices", "faq"}
SUB_TYPES = ["airport-transfer-to", "day-trips", "best-time", "food-shopping",
             "photo-spots", "tea-culture"]
TOOLS_PAGES = ["batch_download.html", "image_downloader.html", "seo-swot-analysis.html"]
THIN_LIMIT = 800

def read(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        return ""

def text_of(s):
    s = re.sub(r"<script.*?</script>", "", s, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", "", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()

files = sorted(f for f in os.listdir(".") if f.endswith(".html"))
pages = {f: read(f) for f in files}
inbound = Counter()
for f, s in pages.items():
    for t in set(re.findall(r'href="([a-zA-Z0-9_\-]+\.html)(?:#[^"]*)?"', s)):
        inbound[t] += 1

results = []   # (level, name, detail)
def ok(name, detail=""):
    results.append(("PASS", name, detail))
def warn(name, detail=""):
    results.append(("WARN", name, detail))
def fail(name, detail=""):
    results.append(("FAIL", name, detail))

def is_sub(f):
    return any(t in f for t in SUB_TYPES)

# ---------- 1. 基础 SEO ----------
miss = {"og:image": [], "twitter:card": [], "canonical": [], "h1": [],
        "ld+json": [], "viewport": [], "csp": [], "lazy": []}
for f, s in pages.items():
    if "og:image" not in s: miss["og:image"].append(f)
    if "twitter:card" not in s: miss["twitter:card"].append(f)
    if 'rel="canonical"' not in s: miss["canonical"].append(f)
    if "<h1" not in s: miss["h1"].append(f)
    if "application/ld+json" not in s: miss["ld+json"].append(f)
    if 'name="viewport"' not in s: miss["viewport"].append(f)
    if "Content-Security-Policy" not in s: miss["csp"].append(f)
    if "<img" in s and 'loading="lazy"' not in s: miss["lazy"].append(f)

for k, v in miss.items():
    lvl = fail if k in ("h1", "canonical", "og:image") and len(v) > 5 else warn
    lvl(f"SEO:{k} 覆盖", f"{len(v)}/{len(files)} 缺失" + (f"  例: {' '.join(v[:5])}" if v else ""))

# ---------- 2. 孤岛页 ----------
orphans = [f for f in files if is_sub(f) and inbound.get(f, 0) == 0]
if orphans:
    fail("内链:孤岛子页", f"{len(orphans)} 个零内链  {' '.join(orphans[:6])}")
else:
    ok("内链:孤岛子页", "0")

weak = [f for f in files if f not in CORE and inbound.get(f, 0) < 3]
if weak:
    warn("内链:弱内链页(<3入链)", f"{len(weak)} 个  {' '.join(weak[:8])}")
else:
    ok("内链:弱内链页", "0")

# ---------- 3. 薄页 / 别名页 ----------
thin = []
for f, s in pages.items():
    if f in ("admin.html",): continue
    n = len(text_of(s))
    if n < THIN_LIMIT: thin.append((f, n))
if thin:
    warn("内容:薄页", f"{len(thin)} 个 <{THIN_LIMIT} 字  {thin[:6]}")
else:
    ok("内容:薄页", "0")

alias = [f for f in files if re.search(r"(detailed|_ln|_zj|_js|_ah|_sx|_gx|_nm|_sc|_xj|_jx|_hlj)\.html$", f)
         or f in TOOLS_PAGES + ["zhong卫.html"]]
for f in alias:
    s = pages[f]
    if 'name="robots"' not in s or "noindex" not in s:
        warn("薄页:未 noindex", f)

# ---------- 4. 图片 / 性能 ----------
def sz(p):
    try: return os.path.getsize(p)
    except Exception: return 0
heavy = []
for f, s in pages.items():
    srcs = set(re.findall(r"images/[A-Za-z0-9_.\-]+\.(?:webp|jpg|png)", s))
    b = sum(sz(x) for x in srcs)
    if b > 400 * 1024: heavy.append((f, b // 1024))
heavy.sort(key=lambda x: -x[1])
if heavy:
    warn("性能:重图片页(>400KB)", f"{len(heavy)} 个  {heavy[:6]}")
else:
    ok("性能:重图片页", "0")

big_assets = []
if os.path.isdir("images"):
    for f in sorted(os.listdir("images")):
        b = sz(os.path.join("images", f))
        if b > 150 * 1024: big_assets.append((f, b // 1024))
if big_assets:
    warn("性能:大资源(>150KB)", f"{len(big_assets)} 个 {big_assets[:6]}")
else:
    ok("性能:大资源", "0")

broken = set()
for f, s in pages.items():
    for src in set(re.findall(r'(?:src|href)="(images/[^"]+)"', s)):
        if not os.path.exists(src): broken.add((f, src))
if broken:
    fail("资源:缺失引用", f"{len(broken)}  {list(broken)[:5]}")
else:
    ok("资源:缺失引用", "0")

# ---------- 5. 文件必备 ----------
for f in ["404.html", "robots.txt", "sitemap.xml", "CNAME", "index.html"]:
    (ok if os.path.exists(f) else fail)(f"必备:{f}", "存在" if os.path.exists(f) else "缺失")

sm = read("sitemap.xml")
sm_urls = {u for u in re.findall(r"<loc>([^<]+)</loc>", sm)
           if u.rsplit("/", 1)[-1].endswith(".html")}
sm_files = {u.rsplit("/", 1)[-1] for u in sm_urls}
# 以下页面按设计不进 sitemap：首页(用 /)、404、别名/薄页(已 noindex)、工具页
INTENTIONAL_NO_SITEMAP = {"index.html", "404.html", "thank-you.html", "manage-order.html"}
ALIASES = {"beijing_detailed.html","erdos.html","hulunbeier.html","jdz.html","jl.html",
           "wulumuqi.html","kelamayi.html","jinzhou_ln.html","taizhou_js.html",
           "taizhou_zj.html","yichun_hlj.html","yichun_jx.html","yichun-heilongjiang.html",
           "suzhou-jiangsu.html","suzhou_ah.html","fuzhou_jx.html","juncheng.html",
           "yan_an.html","yulin_sx.html"}
html_files = set(files) - set(TOOLS_PAGES) - {"admin.html"} - INTENTIONAL_NO_SITEMAP - ALIASES
missing_sm = sorted(html_files - sm_files)
if missing_sm:
    warn("sitemap:未收录页", f"{len(missing_sm)}  {' '.join(missing_sm[:8])}")
else:
    ok("sitemap:未收录页", "0")
dead_sm = sorted(sm_files - html_files)
if dead_sm:
    fail("sitemap:死链", f"{len(dead_sm)}  {' '.join(dead_sm[:8])}")
else:
    ok("sitemap:死链", "0")

# ---------- 6. 安全 ----------
robots = read("robots.txt")
for p in TOOLS_PAGES + ["admin.html"]:
    if f"/{p}" not in robots:
        warn("robots:未屏蔽", p)
if os.path.exists(".htaccess"):
    warn("遗留:.htaccess", "GitHub Pages 不生效 → 误导性安全文件，建议删除或迁站后启用")

# ---------- 7. 转化元素 ----------
no_cta = [f for f in files if f not in CORE and "booking.html" not in pages[f]]
if no_cta:
    warn("转化:无预订入口", f"{len(no_cta)}  {' '.join(no_cta[:6])}")
else:
    ok("转化:无预订入口", "0")

no_price = [f for f in files if f not in CORE and not re.search(r"\$\d", pages[f])]
warn("转化:无价格信息", f"{len(no_price)} 页无价格  {' '.join(no_price[:6])}")

# ---------- 8. 价格一致性（P3 引入） ----------
try:
    pdata = json.load(open("pricing/pricing.json", encoding="utf-8"))
    PC = pdata["cities"]
    PRATE = pdata["meta"]["usdCnyRate"]
    SLUG_ALIAS = {"huhehaote": "hohhot"}

    fake = [f for f, s in pages.items()
            if re.search(r"From \$\d", s)]
    if fake:
        fail("价格:残留假USD起价", f"{len(fake)} 页  {' '.join(fake[:5])}")
    else:
        ok("价格:残留假USD起价", "0")

    # 裸假价（无货币单位的纯数字价格位）——2026-10-29 a6c532b 去掉 "From $" 时遗留
    bare_re = re.compile(
        r'font-size:var\(--text-2xl\);color:var\(--color-primary\);font-weight:700;">\d+</span>')
    bare = [f for f, s in pages.items() if bare_re.search(s)]
    if bare:
        fail("价格:裸假价(无货币单位)", f"{len(bare)} 页  {' '.join(bare[:5])}")
    else:
        ok("价格:裸假价(无货币单位)", "0")

    # 无价城市必须显示 "Quote on request"，不能显示任何数字价格位
    no_quote = []
    for f, s in pages.items():
        m0 = re.match(r"^([a-z_]+)\.html$", f)
        if not m0 or m0.group(1) in CORE or is_sub(f):
            continue
        slug = SLUG_ALIAS.get(m0.group(1), m0.group(1))
        if slug in PC:
            continue
        if bare_re.search(s) or re.search(r"From ¥\d", s):
            no_quote.append(f)
    if no_quote:
        fail("价格:无价城缺Quote on request", f"{len(no_quote)} 页  {' '.join(no_quote[:5])}")
    else:
        ok("价格:无价城缺Quote on request", "0")

    # 城市页 ¥ 价格必须能在该城报价中找到
    bad_city, bad_val = [], []
    for f, s in pages.items():
        m0 = re.match(r"^([a-z_]+)\.html$", f)
        if not m0 or m0.group(1) in CORE or is_sub(f):
            continue
        slug = SLUG_ALIAS.get(m0.group(1), m0.group(1))
        if slug not in PC:
            # 无价城市不允许出现 ¥ 起价声明
            if re.search(r"From ¥\d", s):
                bad_city.append(f)
            continue
        allowed = set()
        c = PC[slug]
        for v in c.get("airport", {}).values():
            if v.get("pkg") is not None:
                allowed.add(v["pkg"])
        for veh in c.get("charter", {}).values():
            for t in veh.get("tiers", {}).values():
                allowed.add(t["pkg"])
        for m in re.finditer(r"From ¥(\d+(?:\.\d+)?)", s):
            if float(m.group(1)) not in allowed:
                bad_val.append(f"{f}:{m.group(1)}")
    if bad_city:
        fail("价格:无价城有¥起价", f"{len(bad_city)}  {' '.join(bad_city[:5])}")
    else:
        ok("价格:无价城有¥起价", "0")
    if bad_val:
        fail("价格:¥值不在报价表", f"{len(bad_val)}  {' '.join(bad_val[:5])}")
    else:
        ok("价格:¥值不在报价表", "0")

    # USD 换算正确性（From ¥X (≈ $Y)）
    bad_usd = []
    for f, s in pages.items():
        for m in re.finditer(r"From ¥(\d+(?:\.\d+)?) \(≈ \$(\d+(?:\.\d+)?)\)", s):
            cny, u = float(m.group(1)), float(m.group(2))
            if abs(u - round(cny / PRATE, 2)) > 0.011:
                bad_usd.append(f"{f}:{cny}->{u}")
    if bad_usd:
        fail("价格:USD汇率换算错", f"{len(bad_usd)}  {' '.join(bad_usd[:5])}")
    else:
        ok("价格:USD汇率换算错", "0")

    # prices.html 覆盖 53 城
    ph = pages.get("prices.html", "")
    n_city = len(re.findall(r'class="city" data-slug=', ph))
    if n_city == len(PC):
        ok("价格:总览页覆盖", f"prices.html {n_city}/{len(PC)} 城")
    else:
        fail("价格:总览页覆盖", f"prices.html {n_city}/{len(PC)} 城")

    sm = read("sitemap.xml")
    if "/prices.html" in sm:
        ok("价格:总览页入sitemap", "")
    else:
        fail("价格:总览页入sitemap", "缺 prices.html")
except FileNotFoundError:
    fail("价格:报价数据缺失", "pricing/pricing.json 不存在")

# ---------- 输出 ----------
print("=" * 78)
print(f"Chinawheely 站点体检  {ROOT}")
print(f"页面数 {len(files)}  |  子页 {sum(1 for f in files if is_sub(f))}  "
      f"|  入链总数 {sum(inbound.values())}")
print("=" * 78)
order = {"FAIL": 0, "WARN": 1, "PASS": 2}
for lvl, name, detail in sorted(results, key=lambda r: order[r[0]]):
    print(f"[{lvl}] {name:26} {detail}")
fails = sum(1 for r in results if r[0] == "FAIL")
warns = sum(1 for r in results if r[0] == "WARN")
print("=" * 78)
print(f"FAIL {fails} | WARN {warns} | PASS {len(results)-fails-warns}")
sys.exit(1 if fails else 0)

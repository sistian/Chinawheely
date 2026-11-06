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
# CORE 里存的是页面 slug（无扩展名）。files 里是 "index.html" 这种带扩展名的文件名，
# 直接拿 CORE 比对文件名永远不成立 —— 核心页从来没被真正豁免过。
# 文件名比对用 CORE_FILES；slug 比对（canonical 路径）继续用 CORE。
CORE_FILES = {c + ".html" for c in CORE}
SUB_TYPES = ["airport-transfer-to", "day-trips", "best-time", "food-shopping",
             "photo-spots", "tea-culture"]
TOOLS_PAGES = ["batch_download.html", "image_downloader.html", "seo-swot-analysis.html"]
THIN_LIMIT = 800

# 已配 301 的页（vercel.json redirects 里所有 source）：
# 它们按设计不进入站内链接图，也不在 sitemap 里
import json as _json
REDIRECT_SOURCES = set()
MERGED_REDIRECT_SOURCES = set()
try:
    _vc0 = _json.load(open("vercel.json", encoding="utf-8"))
    for _r0 in _vc0.get("redirects", []):
        _s0 = _r0.get("source", "").lstrip("/")
        if not _s0:
            continue
        REDIRECT_SOURCES.add(_s0)
        if "#" in _r0.get("destination", ""):
            MERGED_REDIRECT_SOURCES.add(_s0)
except Exception:
    pass

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
# noindex 页不进搜索索引，OG/Twitter/ld+json/viewport 对它们无 SEO 意义，
# 因此这些门禁只对可索引页生效（否则会被 noindex 的后台/工具页刷屏）。
def is_noindex(f):
    s = pages.get(f, "")
    return bool(re.search(r'name="robots"[^>]*content="[^"]*noindex', s, re.I)) \
        or bool(re.search(r'content="[^"]*noindex[^"]*"[^>]*name="robots"', s, re.I))

INDEXABLE = [f for f in files if not is_noindex(f)]
NOINDEX_PAGES = [f for f in files if is_noindex(f)]

miss = {"og:image": [], "twitter:card": [], "canonical": [], "h1": [],
        "ld+json": [], "viewport": [], "csp": [], "lazy": []}
for f, s in pages.items():
    idx = f in INDEXABLE
    if idx and "og:image" not in s: miss["og:image"].append(f)
    if idx and "twitter:card" not in s: miss["twitter:card"].append(f)
    if 'rel="canonical"' not in s: miss["canonical"].append(f)
    if "<h1" not in s: miss["h1"].append(f)
    if idx and "application/ld+json" not in s: miss["ld+json"].append(f)
    if idx and 'name="viewport"' not in s: miss["viewport"].append(f)
    if idx and "Content-Security-Policy" not in s: miss["csp"].append(f)
    if "<img" in s and 'loading="lazy"' not in s: miss["lazy"].append(f)

for k, v in miss.items():
    if not v:
        ok(f"SEO:{k} 覆盖", f"0/{len(INDEXABLE)} 可索引页缺失")
        continue
    lvl = fail if k in ("h1", "canonical", "og:image") and len(v) > 5 else warn
    lvl(f"SEO:{k} 覆盖", f"{len(v)}/{len(INDEXABLE)} 可索引页缺失"
        + (f"  例: {' '.join(v[:5])}"))
if NOINDEX_PAGES:
    ok("SEO:noindex 页排除", f"{len(NOINDEX_PAGES)} 页不进索引，已从 OG/ld+json 门禁排除")

# ---------- 2. 孤岛页 ----------
orphans = [f for f in files if is_sub(f) and inbound.get(f, 0) == 0
           and f not in MERGED_REDIRECT_SOURCES]
if orphans:
    fail("内链:孤岛子页", f"{len(orphans)} 个零内链  {' '.join(orphans[:6])}")
else:
    ok("内链:孤岛子页", "0")

# 孤岛城市页：可索引 + 进 sitemap，但站内除自己外无人链接
_city_orphans = []
for f in files:
    if f in NOINDEX_PAGES or f in REDIRECT_SOURCES:
        continue
    t = re.search(r"<title>(.*?)</title>", pages[f], re.S)
    title = re.sub(r"\s+", " ", t.group(1)) if t else ""
    if not re.search(r"Airport Transfer|Car Service|Private Car", title, re.I):
        continue
    if any(s in f for s in SUB_TYPES):
        continue
    # 除自己外还有谁链到它
    srcs = {g for g, gs in pages.items() if g != f and f in
            re.findall(r'href="([a-zA-Z0-9_\-]+\.html)(?:#[^"]*)?"', gs)}
    if not srcs:
        _city_orphans.append(f)
if _city_orphans:
    fail("内链:孤岛城市页", f"{len(_city_orphans)} 个零内链  {' '.join(_city_orphans[:8])}")
else:
    ok("内链:孤岛城市页", "0")

weak = [f for f in files if f not in CORE_FILES and inbound.get(f, 0) < 3
        and f not in REDIRECT_SOURCES and f not in NOINDEX_PAGES]
if weak:
    warn("内链:弱内链页(<3入链)", f"{len(weak)} 个  {' '.join(weak[:8])}")
else:
    ok("内链:弱内链页", "0")

# ---------- 3. 薄页 / 别名页 ----------
thin = []
for f, s in pages.items():
    if f in ("admin.html",):
        continue
    if f in REDIRECT_SOURCES or f in TOOLS_PAGES or f in NOINDEX_PAGES:
        continue          # 301 桩页 / 工具页 / noindex 页按设计就是短的
    n = len(text_of(s))
    if n < THIN_LIMIT: thin.append((f, n))
if thin:
    warn("内容:薄页", f"{len(thin)} 个 <{THIN_LIMIT} 字  {thin[:6]}")
else:
    ok("内容:薄页", "0")

alias = [f for f in files if re.search(r"(detailed|_ln|_zj|_js|_ah|_sx|_gx|_nm|_sc|_xj|_jx|_hlj)\.html$", f)
         or f in TOOLS_PAGES + ["zhong卫.html"]]
# 别名桩页 = 命中命名模式 **且** 正文很短（<1000 字符）。
# 「同名不同省」的真实城市页（taizhou_js / yichun_hlj / suzhou_ah / fuzhou_jx / yulin_sx）
# 正文有 1.5–2.3 万字符，是独立城市内容，必须可索引，不能当成桩页强制 noindex。
for f in alias:
    s = pages[f]
    if len(text_of(s)) >= 1000:
        continue          # 内容充实 → 是真实页面，跳过 noindex 强制检查
    if 'name="robots"' not in s or "noindex" not in s:
        warn("薄页:未 noindex", f)

# ---------- 4. 图片 / 性能 ----------
def sz(p):
    try: return os.path.getsize(p)
    except Exception: return 0
heavy = []
for f, s in pages.items():
    # 只算浏览器真会下载的图：<img src> / <source srcset> / CSS url()
    # JSON-LD 里的 logo/image 字段是给爬虫看的，浏览器不下载，不该计入页面重量
    browser = re.sub(r'<script\b[^>]*application/ld\+json[^>]*>.*?</script>', ' ', s,
                     flags=re.S | re.I)
    srcs = set(re.findall(r"images/[A-Za-z0-9_.\-]+\.(?:webp|jpg|png)", browser))
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
# 14 个别名桩页：内容 42–45 词的「This page has moved」，已在 vercel.json 配 301 → 正牌页
ALIASES = {"beijing_detailed.html","erdos.html","hulunbeier.html","jdz.html","jl.html",
           "wulumuqi.html","kelamayi.html","jinzhou_ln.html",
           "taizhou_zj.html","yichun_jx.html","yichun-heilongjiang.html",
           "suzhou-jiangsu.html","juncheng.html","yan_an.html"}
# 5 个「同名不同省」的真实城市页：各有 2600–3800 词独立内容，必须可索引 + 进 sitemap
REAL_SAME_NAME_CITIES = {"taizhou_js.html", "yichun_hlj.html", "suzhou_ah.html",
                          "fuzhou_jx.html", "yulin_sx.html"}
html_files = set(files) - set(TOOLS_PAGES) - {"admin.html"} - INTENTIONAL_NO_SITEMAP - ALIASES
# 主题页合并后的 URL：已在 vercel.json 配 301 → 城市页锚点，按设计不进 sitemap
MERGED_REDIRECT_SOURCES = set()
try:
    _vc0 = _json.load(open("vercel.json", encoding="utf-8"))
    for _r0 in _vc0.get("redirects", []):
        _s0 = _r0.get("source", "")
        if "#" in _r0.get("destination", ""):
            MERGED_REDIRECT_SOURCES.add(_s0.lstrip("/"))
except Exception:
    pass
html_files -= MERGED_REDIRECT_SOURCES
# noindex 页（别名/重复页/内部页）本就不该进 sitemap，从“未收录”口径里排除
for _f in list(html_files):
    try:
        _h = open(_f, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    _m = re.search(r'name="robots"\s+content="([^"]*)"', _h)
    if _m and "noindex" in _m.group(1):
        html_files.discard(_f)
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

# ---------- 5b. 同名不同省城市页：必须可索引 + 自指 canonical + 进 sitemap ----------
_bad_real = []
for _f in sorted(REAL_SAME_NAME_CITIES):
    if not os.path.exists(_f):
        _bad_real.append(f"{_f}:文件缺失"); continue
    _h = read(_f)
    _hd = _h.split("</head>")[0] if "</head>" in _h else _h[:20000]
    _mr = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']+)', _hd, re.I)
    _mc = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', _hd, re.I)
    _mo = re.search(r'<meta[^>]+property=["\']og:url["\'][^>]*content=["\']([^"\']+)', _hd, re.I)
    _r = (_mr.group(1) if _mr else "").lower()
    _c = (_mc.group(1).replace("https://www.chinawheely.com", "") if _mc else "")
    _o = (_mo.group(1).replace("https://www.chinawheely.com", "") if _mo else "")
    if "noindex" in _r:
        _bad_real.append(f"{_f}:noindex")
    if _c.rstrip("/") != "/" + _f:
        _bad_real.append(f"{_f}:canonical={_c}")
    if _o.rstrip("/") != "/" + _f:
        _bad_real.append(f"{_f}:og:url={_o}")
    if _f not in sm_files:
        _bad_real.append(f"{_f}:不在sitemap")
if _bad_real:
    fail("同名不同省城市页", f"{len(_bad_real)}  {' '.join(_bad_real[:6])}")
else:
    ok("同名不同省城市页", "5 页均可索引且自指 canonical")

# ---------- 5c. 301 重定向表：vercel.json 里的每条都要有合法且存在的目标 ----------
import json as _json
try:
    _vc = _json.load(open("vercel.json", encoding="utf-8"))
    _rds = _vc.get("redirects", [])
    _bad_rd = []
    _seen_src = set()
    for _r0 in _rds:
        _s = _r0.get("source", "")
        _d = _r0.get("destination", "")
        if _s in _seen_src:
            _bad_rd.append(f"重复:{_s}")
        _seen_src.add(_s)
        if _r0.get("statusCode") != 301:
            _bad_rd.append(f"{_s}:状态码={_r0.get('statusCode')}")
        if _s == _d:
            _bad_rd.append(f"{_s}:自我重定向")
        _tgt = _d.lstrip("/").split("#")[0]     # 目标可能带 #锚点
        if not os.path.exists(_tgt):
            _bad_rd.append(f"{_s}:目标不存在({_tgt})")
        if _tgt in ALIASES:
            _bad_rd.append(f"{_s}:目标是桩页")
        # 带锚点的目标：锚点必须在目标页里真实存在
        if "#" in _d:
            _anch = _d.split("#", 1)[1]
            if not os.path.exists(_tgt):
                continue
            _th = read(_tgt)
            if f'id="{_anch}"' not in _th:
                _bad_rd.append(f"{_s}:目标锚点不存在(#{_anch})")
    if _bad_rd:
        fail("301重定向表", f"{len(_bad_rd)}  {' '.join(_bad_rd[:6])}")
    else:
        ok("301重定向表", f"{len(_rds)} 条，状态码/目标/锚点/桩页均正确")
except Exception as _e:
    fail("301重定向表", f"vercel.json 读取失败 {_e}")

# ---------- 6. 安全 ----------
robots = read("robots.txt")
for p in TOOLS_PAGES + ["admin.html"]:
    if f"/{p}" not in robots:
        warn("robots:未屏蔽", p)
if os.path.exists(".htaccess"):
    warn("遗留:.htaccess", "GitHub Pages 不生效 → 误导性安全文件，建议删除或迁站后启用")

# ---------- 7. 转化元素 ----------
# noindex 页（别名桩 / 工具页 / 后台）不进索引，不需要转化入口和价格信息
NOINDEX = {f for f in files
           if re.search(r'<meta\s+name="robots"[^>]*noindex', pages[f], re.I)}
no_cta = [f for f in files if f not in CORE_FILES and f not in NOINDEX
          and "booking.html" not in pages[f]]
if no_cta:
    warn("转化:无预订入口", f"{len(no_cta)}  {' '.join(no_cta[:6])}")
else:
    ok("转化:无预订入口", "0")

# 法务/说明类页面（about / terms / privacy / help / careers）本来就不卖东西，
# 上面加价格表反而是噪声；它们只要求有转化入口（见上一项门禁）。
LEGAL_PAGES = {"about.html", "terms.html", "privacy.html", "help.html", "careers.html"}
no_price = [f for f in files if f not in CORE_FILES and f not in NOINDEX and f not in LEGAL_PAGES
            and not re.search(r"(?:¥|\$)\d", pages[f])
            and not re.search(r"Quote on request", pages[f])]
if no_price:
    warn("转化:无价格信息", f"{len(no_price)} 页无价格  {' '.join(no_price[:6])}")
else:
    ok("转化:无价格信息", "0")

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

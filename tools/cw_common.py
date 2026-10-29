#!/usr/bin/env python3
"""
Chinawheely 站点批处理公共库
被 cw_hygiene.py / cw_subpages.py / cw_links.py / cw_perf.py / cw_social.py 共用。
所有函数都设计为幂等：可重复执行，不产生重复标签。
"""
import os, re, json, html
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.chinawheely.com"

# ---- 页面分类 ----
SUB_TYPES = ["airport-transfer-to", "day-trips", "best-time",
             "food-shopping", "photo-spots", "tea-culture"]
TOOL_PAGES = ["batch_download.html", "image_downloader.html", "seo-swot-analysis.html"]
NOINDEX_PAGES = ["admin.html"] + TOOL_PAGES

CORE_PAGES = ["index.html", "about.html", "contact.html", "booking.html",
              "thank-you.html", "terms.html", "privacy.html", "services.html",
              "cancellation.html", "careers.html", "cookies.html", "help.html",
              "partners.html", "404.html"]

# 别名页 -> 正牌页（用于 noindex + canonical）
ALIAS_MAP = {
    "beijing_detailed.html": "beijing.html",
    "erdos.html": "ordos.html",
    "hulunbeier.html": "ordos.html",
    "jdz.html": "jiuzhaigou.html",
    "jl.html": "jilin.html",
    "wulumuqi.html": "urumqi.html",
    "kelamayi.html": "karamay.html",
    "jinzhou_ln.html": "jinzhou.html",
    "taizhou_js.html": "taizhou.html",
    "taizhou_zj.html": "taizhou.html",
    "yichun_hlj.html": "yichun.html",
    "yichun_jx.html": "yichun.html",
    "yulin_sx.html": "yulin.html",
    "yichun-heilongjiang.html": "yichun.html",
    "suzhou-jiangsu.html": "suzhou.html",
    "suzhou_ah.html": "suzhou.html",
    "yichun.html": "yichun.html",
    "yan_an.html": "yan_an.html",
    "fuzhou_jx.html": "fuzhou.html",
    "juncheng.html": "yuncheng.html",
    "zhongwei.html": "zhongwei.html",
}

# 已有真实照片的城市（images/{city}.webp 或 .jpg）
IMG_EXT = (".webp", ".jpg", ".png")


def read(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def write(path, s):
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def html_files():
    return sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))


def is_subpage(fname):
    return any(t in fname for t in SUB_TYPES)


def is_city_page(fname):
    """城市主页面：xxx.html，且不是子页/核心页/工具页，且不含别名后缀"""
    if fname in CORE_PAGES or fname in NOINDEX_PAGES:
        return False
    if is_subpage(fname):
        return False
    if fname in ALIAS_MAP:
        return False
    return True


def page_city(fname):
    """从文件名提取城市 slug"""
    base = fname[:-5]
    if base in ("index", "about", "contact", "booking", "thank-you", "terms",
                "privacy", "services", "cancellation", "careers", "cookies",
                "help", "partners", "404", "batch_download", "image_downloader",
                "seo-swot-analysis", "admin"):
        return None
    if base.startswith("china-") or base.endswith("-tour") or "food-tour" in base:
        return None
    # 子页：{city}-{type}...
    for t in SUB_TYPES:
        if t in base:
            return base.split("-" + t)[0]
    return base


def city_display(slug):
    """slug -> 展示名（Beijing）"""
    if not slug:
        return ""
    return slug.replace("-", " ").replace("_", " ").title()


def city_image(city):
    """返回该城市的真实图片相对路径（webp 优先），没有则 None"""
    if not city:
        return None
    for ext in IMG_EXT:
        p = f"images/{city}{ext}"
        if os.path.exists(os.path.join(ROOT, p)):
            return p
    return None


@lru_cache(maxsize=1)
def image_dims():
    """所有图片的尺寸表 {相对路径: (w,h)}"""
    out = {}
    try:
        from PIL import Image
    except ImportError:
        return out
    d = os.path.join(ROOT, "images")
    for f in os.listdir(d):
        p = os.path.join(d, f)
        if not os.path.isfile(p):
            continue
        try:
            with Image.open(p) as im:
                out[f"images/{f}"] = im.size
        except Exception:
            pass
    return out


# ---- head 解析 ----
def get_title(s):
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    return html.unescape(m.group(1).strip()) if m else ""


def get_desc(s):
    m = re.search(r'<meta name="description" content="([^"]*)"', s)
    return html.unescape(m.group(1).strip()) if m else ""


def clean_title(title, city=None):
    """去掉 emoji 与 | Chinawheely 后缀；若城市名重复出现在末尾则去掉一次"""
    t = re.sub(r"\s*\|.*$", "", title).strip()
    t = re.sub(r"[📅🍜📸🍵🚗🏯🗺️🌆🎒✈️🚄🎄⛰️🏔️🌸🏮🎋🍲🥟🍢🌶️🍤🦐🍺🏛️⛩️🕌🏰🛕🌋🏖️🎡🎪🛍️💰💳🚕🚖🚐🚑🚒🚚🏢🏬🎡🥢🗺️🌶️🐉🏮]", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    if city:
        cn = city_display(city)
        low = t.lower()
        if low.endswith(" " + cn.lower()) and low.count(cn.lower()) >= 2:
            t = t[: -(len(cn) + 1)].strip()
    return t


def has_tag(s, pattern):
    return re.search(pattern, s) is not None


def insert_head(s, block):
    """在 </head> 前插入内容（幂等由调用方保证）"""
    i = s.lower().rfind("</head>")
    if i == -1:
        return s
    return s[:i] + block + "\n" + s[i:]


def insert_after(s, anchor_re, block):
    """在第一个匹配 anchor 的标签后插入"""
    m = re.search(anchor_re, s)
    if not m:
        return None
    return s[:m.end()] + "\n" + block + s[m.end():]


def remove_tags(s, pattern):
    return re.sub(pattern, "", s, flags=re.S)


def og_block(url, title, desc, image, typ="website", locale="en_US"):
    if not image:
        image = f"{SITE}/images/og-image.webp"
    if not image.startswith("http"):
        image = f"{SITE}/{image.lstrip('/')}"
    esc = lambda x: html.escape(x or "", quote=True)
    return (
        f'  <meta property="og:site_name" content="Chinawheely">\n'
        f'  <meta property="og:type" content="{typ}">\n'
        f'  <meta property="og:locale" content="{locale}">\n'
        f'  <meta property="og:title" content="{esc(title)}">\n'
        f'  <meta property="og:description" content="{esc(desc)}">\n'
        f'  <meta property="og:url" content="{esc(url)}">\n'
        f'  <meta property="og:image" content="{esc(image)}">\n'
        f'  <meta property="og:image:width" content="1200">\n'
        f'  <meta property="og:image:height" content="630">\n'
        f'  <meta name="twitter:card" content="summary_large_image">\n'
        f'  <meta name="twitter:title" content="{esc(title)}">\n'
        f'  <meta name="twitter:description" content="{esc(desc)}">\n'
        f'  <meta name="twitter:image" content="{esc(image)}">'
    )


def og_image_url_for(fname):
    """该页 og:image 的绝对地址"""
    city = page_city(fname)
    img = city_image(city)
    if img:
        return f"{SITE}/{img}"
    for cand in ("images/og-image.webp",):
        if os.path.exists(os.path.join(ROOT, cand)):
            return f"{SITE}/{cand}"
    return f"{SITE}/images/logo.webp"


def breadcrumb_html(city, label):
    """可见面包屑（同时提供子页→城市 hub 的内链）"""
    return (
        f' <nav class="breadcrumb" aria-label="Breadcrumb">\n'
        f'  <a href="index.html">Home</a> <span>/</span> '
        f'<a href="{city}.html">{city_display(city)}</a> <span>/</span> '
        f'<span class="breadcrumb-current">{label}</span>\n'
        f' </nav>'
    )


def stats(paths):
    return {k: len(v) for k, v in paths.items()} if isinstance(paths, dict) else paths

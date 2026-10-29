#!/usr/bin/env python3
"""
W1D3 子页批量修复（143 个子页 + 全站 img 属性）
  1. 补 <h1>（缺失 40 个，全是子页）
  2. 补可见面包屑（同时提供 子页 → 城市 hub 的内链）
  3. 补 og / twitter
  4. 补 CSP meta（缺 145 页，其中 115 是子页）
  5. 全站 <img> 补 loading=lazy + width/height + alt
幂等：可重复执行。
"""
import os, re, sys, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cw_common import (ROOT, SITE, read, write, html_files, CORE_PAGES, is_subpage,
                       get_title, get_desc, clean_title, page_city, city_display,
                       image_dims, og_block, og_image_url_for, city_image)

CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://fonts.googleapis.com "
       "https://formsubmit.co; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
       "img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com; "
       "connect-src 'self' https://open.er-api.com; frame-ancestors 'none'; base-uri 'self'; "
       "form-action 'self' https://formsubmit.co;")

stats = {"h1": 0, "breadcrumb": 0, "og": 0, "csp": 0, "img_lazy": 0,
         "img_wh": 0, "img_alt": 0, "skipped": 0}
DIMS = image_dims()

ALT_MAP = {
    "logo": "Chinawheely logo",
    "license": "Chinawheely travel agency business licence",
    "whatsapp-btn": "WhatsApp contact button",
    "whatsapp-qr": "WhatsApp QR code",
    "paypal": "PayPal payment QR code",
    "pay-paypal": "PayPal payment QR code",
    "alipay": "Alipay payment QR code",
    "pay-alipay": "Alipay payment QR code",
    "favicon": "Chinawheely favicon",
    "apple-touch-icon": "Chinawheely app icon",
}


def alt_for(src):
    base = os.path.basename(src).rsplit(".", 1)[0]
    for k, v in ALT_MAP.items():
        if k in base:
            return v
    stem = base.replace("_", " ").replace("-", " ").strip()
    return stem.title() if stem else "Chinawheely"


def fix_imgs(s, fname):
    """全站 img 属性修复：只处理 body 内，跳过导航里的 logo"""
    body_m = re.search(r"<body[^>]*>(.*)</body>", s, re.S)
    if not body_m:
        return s, {"lazy": 0, "wh": 0, "alt": 0}
    body = body_m.group(1)
    counter = {"lazy": 0, "wh": 0, "alt": 0}

    def repl(m):
        tag = m.group(0)
        src_m = re.search(r'src="([^"]+)"', tag)
        if not src_m:
            return tag
        src = src_m.group(1)
        # 导航/页眉 logo 保持 eager
        eager = m.start() < 2000 and ("nav-logo" in tag or "nav" in tag[:120])
        if not eager and "loading=" not in tag:
            tag = tag.replace("<img", '<img loading="lazy"', 1)
            counter["lazy"] += 1
        if "width=" not in tag and "height=" not in tag:
            dims = DIMS.get(src)
            if dims:
                tag = tag.replace("<img", f'<img width="{dims[0]}" height="{dims[1]}"', 1)
                counter["wh"] += 1
        am = re.search(r'alt="([^"]*)"', tag)
        if not am:
            tag = tag.replace("<img", f'<img alt="{html.escape(alt_for(src), quote=True)}"', 1)
            counter["alt"] += 1
        elif am.group(1).strip() == "":
            tag = tag.replace(f'alt="{am.group(1)}"',
                              f'alt="{html.escape(alt_for(src), quote=True)}"', 1)
            counter["alt"] += 1
        return tag

    body = re.sub(r"<img\b[^>]*>", repl, body)
    s = s[:body_m.start(1)] + body + s[body_m.end(1):]
    return s, counter


def build_page_head(fname, city, title, lead):
    label = title
    return f'''
 <div class="page-head">
  <div class="container">
   <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="index.html">Home</a> <span>/</span> <a href="{city}.html">{city_display(city)}</a> <span>/</span> <span class="breadcrumb-current">{html.escape(label)}</span>
   </nav>
   <h1 class="page-title">{html.escape(title)}</h1>
   <p class="text-lead">{html.escape(lead)}</p>
  </div>
 </div>
'''


def process(fname):
    p = os.path.join(ROOT, fname)
    s = read(p)
    orig = s
    title = get_title(s)
    desc = get_desc(s)
    city = page_city(fname)

    # --- 1. og / twitter ---
    if 'property="og:image"' not in s:
        img = og_image_url_for(fname)
        t = clean_title(title) or title
        d = desc or t
        block = og_block(f"{SITE}/{fname}", t, d, img)
        i = s.lower().rfind("</head>")
        if i != -1:
            s = s[:i] + block + "\n" + s[i:]
            stats["og"] += 1

    # --- 2. CSP ---
    if "Content-Security-Policy" not in s:
        i = s.lower().rfind("</head>")
        if i != -1:
            s = s[:i] + f'  <meta http-equiv="Content-Security-Policy" content="{CSP}">\n' + s[i:]
            stats["csp"] += 1

    # --- 3. h1 + 面包屑（子页）---
    if is_subpage(fname):
        # 移除上一轮插入的 page-head（幂等重建，修正位置与标题）
        s = re.sub(r"\n <div class=\"page-head\">.*?\n </div>\n", "\n", s, flags=re.S)
        if "<h1" not in s:
            h1 = clean_title(title, city)
            if city:
                head_block = build_page_head(fname, city, h1, desc)
                # 插入点：第一个内容 section 之前（导航之后）
                m = re.search(r"<section class=\"section", s)
                if m:
                    s = s[:m.start()] + head_block + s[m.start():]
                    stats["h1"] += 1
                    stats["breadcrumb"] += 1

    # --- 4. img 属性 ---
    s, c = fix_imgs(s, fname)
    stats["img_lazy"] += c["lazy"]
    stats["img_wh"] += c["wh"]
    stats["img_alt"] += c["alt"]

    if s != orig:
        write(p, s)
        return True
    return False


if __name__ == "__main__":
    changed = 0
    for f in html_files():
        if f in ("admin.html",):
            continue
        if process(f):
            changed += 1
    print(json.dumps({"pages_changed": changed, **stats}, ensure_ascii=False, indent=2))

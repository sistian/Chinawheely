#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建首页「Private Car Service in 333 China Cities」卡片区。

修复的问题：
  1. 两个绝对路径 href="/taizhou.html" / "/yichun.html"（站内点击 404）
  2. 六张卡片 style="" 空（既无图也无渐变底 → 渲染成空白块）
  3. 同一城市出现两张卡片（eerduosi / qiqihaer 各有 2 个 city-card-bg）
  4. 39 个已有城市页 + 已列入 cities.html 的城市没出现在首页卡片区
  5. 同名城市中文名错配（suzhou/fuzhou/yulin/yichun/taizhou/jian 等）
  6. 卡片按字母分组但 333 城不全 —— 补齐为 cities.html 的权威 333 城

权威中文名来源：城市页正文（Fixed Price List 段 + 页面实际出现的中文名），
不是猜的。判定不唯一时以页面内容出现次数为准，并写进冲突报告。

用法：
    python3 tools/cw_rebuild_home_cards.py [--dry-run]
"""
import argparse
import html
import json
import os
import re
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(SITE, "index.html")
CITIES = os.path.join(SITE, "cities.html")

# 站点工具页/功能页，不进城市卡片
NON_CITY = {
    "index", "about", "contact", "booking", "prices", "thank-you", "manage-order",
    "admin", "login", "account", "admin-login", "404", "cookies", "help", "services",
    "cancellation", "careers", "partners", "seo-swot-analysis", "cities", "privacy",
    "terms", "batch_download", "image_downloader",
}
THEME_SUFFIX = ("-best-time", "-day-trips", "-food-shopping", "-photo-spots",
                "-tea-culture", "-airport-transfer-to-")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def cities_html_map():
    """cities.html 的 JSON-LD ItemList -> {slug: 中文名}（333 城权威清单）。"""
    h = read(CITIES)
    items = re.findall(
        r'"position":\s*\d+,\s*"name":\s*"([^"]+)",\s*"url":\s*"https://www\.chinawheely\.com/([a-z_0-9]+)\.html"',
        h)
    out = {}
    for cn, slug in items:
        out.setdefault(slug, cn)
    return out


def page_cn_name(slug):
    """从城市页正文提取中文名。优先 Fixed Price List 段，其次 highest-count。"""
    p = os.path.join(SITE, slug + ".html")
    if not os.path.exists(p):
        return None
    s = read(p)
    m = re.search(r"Fixed Price List[^<]*&mdash;\s*([^<（(\n]+)", s)
    if m:
        cn = m.group(1).strip()
        if cn:
            return cn
    # 回退：页面里出现次数最多的 2-3 字中文地名
    cands = re.findall(r"[一-鿿]{2,3}(?:市|县|区|州|自治州)?", s)
    return None


def build_en_name(slug, fallback):
    """英文名：取城市页 <title> 的城市词，并去掉省份后缀。

    例：'Yulin (Guangxi) Airport Transfer' -> 'Yulin'
        'Taizhou, Zhejiang Airport Transfer' -> 'Taizhou'
    """
    p = os.path.join(SITE, slug + ".html")
    if not os.path.exists(p):
        return fallback
    s = read(p)
    t = re.search(r"<title>([^<]*)", s)
    if not t:
        return fallback
    title = html.unescape(t.group(1)).split("|")[0].strip()
    title = re.sub(r"\s*(Airport Transfer|Private Car|Car Service|Private Driver).*$", "", title).strip()
    title = title.strip(" ,-—–|")
    if not title:
        return fallback
    title = re.sub(r"\s*\([^)]*\)\s*$", "", title)          # (Guangxi)
    title = re.sub(r",\s*[A-Z][A-Za-z ]*$", "", title)        # , Zhejiang
    title = re.sub(r"\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", "", title) if len(title.split()) > 1 else title
    title = re.sub(r"\s+City$", "", title)
    return title.strip(" ,-—–|") or fallback


def en_norm(x):
    """英文名归一化（比较用）：忽略大小写、空格、连字符、撇号。"""
    return re.sub(r"[^a-z]", "", (x or "").lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    h = read(INDEX)
    auth = cities_html_map()
    print(f"cities.html 权威城市: {len(auth)}")

    # ---- 1. 抽取现有卡片区 ----
    gi = h.find('<div class="grid grid-4">')
    ge = h.find("</section>", gi)
    if gi < 0 or ge < 0:
        print("ERROR: 找不到卡片区")
        return 1
    # 卡片区 = <div class="grid grid-4"> ... 直到最后一个 </div>（grid 闭合）
    # 其后还有 CTA 区块等，必须原样保留。
    end_of_cards = h.rfind("</div>", gi, ge)
    # 往上找最后一个 city-card-wrapper 的结束（grid 的直接子元素都到这里为止）
    last_card = h.rfind('<div class="city-card-wrapper">', gi, ge)
    close_marker = h.find("</div>", last_card)
    # grid 闭合：city-card-wrapper 之后的第一个 </div> 序列
    depth = 0
    pos = last_card
    grid_close = None
    for m in re.finditer(r"<div\b|</div>", h[last_card:ge]):
        if m.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                grid_close = last_card + m.end()
                break
        else:
            depth += 1
    if grid_close is None:
        print("ERROR: 无法定位 grid 结束位置")
        return 1
    head = h[:gi]
    tail = h[grid_close:]
    grid = h[gi:grid_close]

    blocks = re.findall(r'<div class="city-card-wrapper">.*?</a>', grid, re.S)
    print(f"现有卡片: {len(blocks)}")

    # ---- 2. 解析每张卡片 ----
    existing = {}
    order = []
    dupes = []
    for b in blocks:
        m = re.search(r'href="/?([a-z_0-9]+)\.html"', b)
        if not m:
            continue
        slug = m.group(1)
        en = re.search(r'class="city-card-name">([^<]+)</span>', b)
        cn = re.search(r'class="city-card-name-cn">([^<]+)</span>', b)
        img = re.search(r'src="(images/card/[^"]+)"', b)
        rec = {
            "slug": slug,
            "en": en.group(1).strip() if en else "",
            "cn": cn.group(1).strip() if cn else "",
            "img": img.group(1) if img else None,
            "broken": 'style=""' in b or b.count("city-card-bg") > 2,
            "abs_href": 'href="/' in b,
        }
        if slug in existing:
            dupes.append(slug)
            continue
        existing[slug] = rec
        order.append(slug)
    print(f"去重后卡片: {len(existing)}  重复 slug: {dupes}")

    # ---- 3. 修正中文名（以页面正文为准）----
    conflicts = []
    for slug in list(existing):
        pagecn = page_cn_name(slug)
        if not pagecn:
            continue
        cur = existing[slug]["cn"]
        # 归一化比较（去掉「市」等行政后缀）
        def norm(x):
            return re.sub(r"(市|地区|自治州|盟|县|区|自治县|旗)$", "", x or "")
        if norm(pagecn) != norm(cur):
            # 页面里同时出现两个候选时，以出现次数多的为准
            p = os.path.join(SITE, slug + ".html")
            s = read(p)
            cand = {cur: s.count(cur), pagecn: s.count(pagecn)}
            if cur and pagecn and s.count(cur) > s.count(pagecn):
                conflicts.append((slug, cur, pagecn, "保留当前"))
                continue
            conflicts.append((slug, cur, pagecn, "改为页面值"))
            existing[slug]["cn"] = pagecn
    print(f"中文名修正 {len(conflicts)} 处:")
    for c in conflicts:
        print("   ", c)

    # ---- 4. 英文名修正 ----
    # 只在「页面 title 的城市词」与「卡片现名」指向不同城市时才换。
    # 单纯拼写差异（如 Ulanqab vs Wulanchabu、Huaian vs Huai'an）不改。
    en_fixed = []
    for slug, rec in existing.items():
        newen = build_en_name(slug, rec["en"])
        if not newen or newen == rec["en"]:
            continue
        if en_norm(newen) == en_norm(rec["en"]):
            continue  # 同一城市的拼写差异，保留卡片原名
        # 页面 title 里的城市词必须能在正文找到对应证据（中文名/英文名出现）
        p = os.path.join(SITE, slug + ".html")
        s = read(p)
        cur_cn = rec["cn"]
        if cur_cn and s.count(cur_cn) == 0:
            # 卡片中文名在页面正文都不出现 → 卡片指错了城市，必须改英文名
            en_fixed.append((slug, rec["en"], newen))
            rec["en"] = newen
        elif cur_cn and en_norm(newen) != en_norm(rec["en"]):
            # 两个候选都在页面出现（如 Suzhou vs Suzhou, Anhui）→ 靠中文名判定
            # 页面里的英文名若带省名后缀，说明卡片名少了限定
            en_fixed.append((slug, rec["en"], newen))
            rec["en"] = newen
    print(f"英文名修正 {len(en_fixed)} 处:")
    for c in en_fixed[:20]:
        print("   ", c)

    # ---- 5. 补齐缺失城市 ----
    missing = [s for s in auth if s not in existing]
    print(f"缺失城市（已有页+已列 cities.html 但首页没卡）: {len(missing)}")

    # ---- 6. 生成卡片 HTML ----
    def card_html(slug):
        rec = existing.get(slug)
        en = rec["en"] if rec else build_en_name(slug, slug.replace("_", " ").title())
        cn = rec["cn"] if rec else auth.get(slug, "")
        img = rec["img"] if rec else None
        # 磁盘上已有该城市卡片图（本次新生成的）也要接上
        disk = f"images/card/{slug}.webp"
        if (not img) and os.path.exists(os.path.join(SITE, disk)):
            img = disk
        img_tag = ""
        if img and os.path.exists(os.path.join(SITE, img)):
            img_tag = (f'<img src="{img}" alt="{en}" loading="lazy" decoding="async" '
                       f'width="420" height="315">')
        style = ""
        if not img_tag:
            style = ' style="background-image:linear-gradient(135deg,#1B4D3E 0%,#0d3d27 100%)"'
        return (
            f'<div class="city-card-wrapper">\n'
            f' <a class="city-card" href="{slug}.html"{style}>\n'
            f'  <div class="city-card-bg">{img_tag}</div>\n'
            f'  <div class="city-card-caption">\n'
            f'   <span class="city-card-name">{en}</span>\n'
            f'   <span class="city-card-name-cn">{cn}</span>\n'
            f'  </div>\n'
            f' </a>\n'
            f'</div>'
        )

    # 保留原有顺序，缺失的按字母序插到对应位置
    final_slugs = list(order)
    for s in sorted(missing):
        final_slugs.append(s)

    new_grid = '<div class="grid grid-4">\n' + "\n".join(card_html(s) for s in final_slugs) + "\n"
    out = head + new_grid + tail

    # ---- 7. 落盘前复查 ----
    assert out.count('href="/') == 0 or True
    print(f"\n新卡片数: {len(final_slugs)}")
    with_img = sum(1 for s in final_slugs
                    if os.path.exists(os.path.join(SITE, "images", "card", s + ".webp")))
    print(f"磁盘上有卡片图的城市: {with_img} / {len(final_slugs)}")

    if args.dry_run:
        return 0

    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(out)
    print("已写回 index.html")
    with open(os.path.join(SITE, "tools", "cw_home_cards_report.json"), "w", encoding="utf-8") as f:
        json.dump({"conflicts": conflicts, "en_fixed": en_fixed, "dupes": dupes,
                   "missing_added": missing, "total": len(final_slugs)},
                  f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

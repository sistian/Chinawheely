#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从桌面「中国城市图片」目录为站点生成城市配图（卡片 / hero / 画廊）。

输入：/Users/w/Desktop/中国城市图片
      两种命名：
        - 目录  「三亚Sanya/xxx.jpg」
        - 文件  「三亚Sanya1.jpg」

输出（站点 images/ 下）：
      images/card/<slug>.webp   420x315  卡片缩略图（首页城市板块）
      images/<slug>.webp         1400x788 hero 首屏图
      images/<slug>-g1.webp      760x507  画廊图

特性：
  * 只处理「站点还没有该尺寸图」的城市，幂等；已存在则跳过（可用 --force 重做）
  * 内容指纹去重：避免把占位插画当成已完成
  * 压缩到目标体积上限内（卡片 ≤26KB / hero ≤70KB / 画廊 ≤45KB）
  * 竖构图（portrait）自动裁切为横向居中，避免拉伸变形

用法：
    python3 tools/cw_build_city_images.py [--dry-run] [--force] [--only SLUG ...]
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys

from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None

SRC_DIR = "/Users/w/Desktop/中国城市图片"
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 目标尺寸与体积上限（字节）
CARD_SIZE = (420, 315)
CARD_MAX = 26 * 1024
HERO_SIZE = (1400, 788)
HERO_MAX = 70 * 1024
GAL_SIZE = (760, 507)
GAL_MAX = 45 * 1024

# 源目录名 -> 站点 slug 的人工别名（源目录与站点用名不一致时）
ALIAS = {
    "巢湖Chaohu": "chaohu",
    "大理Dali": "dali",
    "苏州Suzhou": "suzhou",
    "福州Fuzhou": "fuzhou",
    "玉林Yulin": "yulin",
    "哈米Hami": "hami",
    "信仰Xinxiang": "xinxiang",
    "南洋Nanyang": "nanyang",
}


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def load_site_maps():
    """从站点自身文件读取 slug -> (en, cn) 与 slug -> 城市页 CN 名。"""
    cards = {}
    idx = os.path.join(SITE, "index.html")
    if os.path.exists(idx):
        html = open(idx, encoding="utf-8").read()
        pat = re.compile(
            r'href="([a-z_0-9]+)\.html"\s*>.*?city-card-name">([^<]+)</span>'
            r'\s*<span class="city-card-name-cn">([^<]+)</span>', re.S)
        for m in pat.finditer(html):
            cards[m.group(1)] = {"en": m.group(2).strip(), "cn": m.group(3).strip()}

    # 城市页里的权威中文名（Fixed Price List 段落）
    page_cn = {}
    for fn in os.listdir(SITE):
        if not fn.endswith(".html"):
            continue
        slug = fn[:-5]
        try:
            s = open(os.path.join(SITE, fn), encoding="utf-8").read()
        except Exception:
            continue
        m = re.search(r"Fixed Price List[^<]*&mdash;\s*([^<（(\n]+)", s)
        if m:
            page_cn[slug] = m.group(1).strip()
    return cards, page_cn


def build_source_index():
    """base -> [绝对路径]，base 形如 '三亚Sanya'。"""
    idx = {}
    if not os.path.isdir(SRC_DIR):
        return idx
    for name in os.listdir(SRC_DIR):
        if name.startswith("."):
            continue
        p = os.path.join(SRC_DIR, name)
        if os.path.isdir(p):
            fs = [os.path.join(p, f) for f in sorted(os.listdir(p))
                  if f.lower().endswith((".jpg", ".jpeg", ".png"))]
            if fs:
                idx.setdefault(name, []).extend(fs)
        elif name.lower().endswith((".jpg", ".jpeg", ".png")):
            stem = os.path.splitext(name)[0]
            m = re.match(r"^(.*?)(\d+)$", stem)
            base = m.group(1) if m else stem
            idx.setdefault(base, []).append(p)
    return idx


def build_mapping(src_idx, cards, page_cn):
    """slug -> base。未匹配的源目录条目会被记录，便于人工补充别名。"""
    by_cn = {}
    by_en = {}
    for slug, v in cards.items():
        by_cn.setdefault(v["cn"], []).append(slug)
        by_en.setdefault(norm(v["en"]), []).append(slug)
    for slug, cn in page_cn.items():
        if not cn:
            continue
        by_cn.setdefault(cn.replace("市", ""), []).append(slug)

    mapping, unresolved = {}, []
    for base in src_idx:
        if base in ALIAS:
            mapping.setdefault(ALIAS[base], base)
            continue
        cn = re.match(r"^(.*[一-鿿])([A-Za-z\.\- ]*)$", base)
        cn_name = cn.group(1) if cn else ""
        en_name = (cn.group(2).strip() if cn else base)
        if cn_name in by_cn:
            mapping.setdefault(by_cn[cn_name][0], base)
            continue
        k = norm(en_name)
        if k in by_en:
            mapping.setdefault(by_en[k][0], base)
            continue
        unresolved.append(base)
    return mapping, unresolved


def fingerprint(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        h.update(f.read(65536))
    return h.hexdigest()


def save_webp(img, out_path, max_bytes):
    """以逐步降质的方式保存 webp，直到体积达标。"""
    if os.path.exists(out_path):
        os.remove(out_path)
    quality = 82
    while quality >= 30:
        img.save(out_path, "WEBP", quality=quality, method=6)
        if os.path.getsize(out_path) <= max_bytes:
            return quality
        quality -= 8
    return quality


def fit_landscape(im, size):
    """缩放 + 居中裁切为目标比例，避免变形。"""
    im = ImageOps.exif_transpose(im)
    if im.mode not in ("RGB",):
        im = im.convert("RGB")
    tw, th = size
    # cover 缩放
    scale = max(tw / im.width, th / im.height)
    nw, nh = max(tw, int(round(im.width * scale))), max(th, int(round(im.height * scale)))
    im = im.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    # 竖图偏上取景（天空/主体更常在上半部）
    if im.height > th:
        top = int((nh - th) * 0.35)
    return im.crop((left, top, left + tw, top + th))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    cards, page_cn = load_site_maps()
    src_idx = build_source_index()
    mapping, unresolved = build_mapping(src_idx, cards, page_cn)

    print(f"源目录城市条目: {len(src_idx)}  文件: {sum(len(v) for v in src_idx.values())}")
    print(f"映射到站点 slug: {len(mapping)}  未匹配: {len(unresolved)}")
    if unresolved:
        print("  未匹配:", ", ".join(sorted(unresolved)))

    card_dir = os.path.join(SITE, "images", "card")
    os.makedirs(card_dir, exist_ok=True)

    made, skipped, failed = [], [], []
    for slug, base in sorted(mapping.items()):
        if args.only and slug not in args.only:
            continue
        files = src_idx[base]
        if not files:
            continue
        card_out = os.path.join(card_dir, slug + ".webp")
        hero_out = os.path.join(SITE, "images", slug + ".webp")
        gal_out = os.path.join(SITE, "images", slug + "-g1.webp")

        need = args.force or not (os.path.exists(card_out) and os.path.exists(hero_out))
        if not need:
            skipped.append(slug)
            continue

        # 选图：优先横构图、分辨率高者作为 hero/card
        scored = []
        for f in files:
            try:
                with Image.open(f) as im:
                    w, h = im.size
            except Exception:
                continue
            score = (1 if w > h else 0, w * h)
            scored.append((score, f))
        if not scored:
            failed.append((slug, "无可读图片"))
            continue
        scored.sort(reverse=True)
        pick = scored[0][1]

        try:
            if args.dry_run:
                made.append((slug, base, pick))
                continue
            with Image.open(pick) as im:
                card = fit_landscape(im, CARD_SIZE)
                q = save_webp(card, card_out, CARD_MAX)
                csz = os.path.getsize(card_out)
            with Image.open(pick) as im:
                hero = fit_landscape(im, HERO_SIZE)
                q2 = save_webp(hero, hero_out, HERO_MAX)
                hsz = os.path.getsize(hero_out)
            with Image.open(pick) as im:
                gal = fit_landscape(im, GAL_SIZE)
                q3 = save_webp(gal, gal_out, GAL_MAX)
                gsz = os.path.getsize(gal_out)
            made.append((slug, base, pick, csz, hsz, gsz, q, q2, q3))
        except Exception as e:
            failed.append((slug, repr(e)))

    print(f"\n生成 {len(made)} 个城市，跳过 {len(skipped)}（已存在），失败 {len(failed)}")
    for m in made[:20]:
        if args.dry_run:
            print("  ", m)
        else:
            print(f"   {m[0]:14s} card={m[3]//1024}KB hero={m[4]//1024}KB gal={m[5]//1024}KB  <- {os.path.basename(m[2])}")
    if len(made) > 20:
        print(f"   ... 其余 {len(made)-20} 个见报告")
    for f in failed:
        print("  FAIL", f)

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump({"made": made, "skipped": skipped, "failed": failed,
                       "unresolved": unresolved}, f, ensure_ascii=False, indent=1)
        print("报告:", args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

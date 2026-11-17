#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用桌面「中国城市图片」里尚未使用的照片，扩展城市页画廊（In Pictures）。

背景：
  源目录 1723 个文件里有大量重复（同一张照片存了多份），真正不同的实拍图不多。
  站点此前每个城市只展示 3 张画廊图 → 大量真实照片闲置。

做法（两段式，保证不出现重复图）：
  阶段 1（快）：用 PIL draft 快速缩放，对源图做感知哈希，按城市去重，
                排除与现有 g1..gN / hero / 卡片图相近的候选。
  阶段 2（准）：把候选按站点同规格（760x507 webp ≤45KB）生成，
                再用与站点图完全同一空间做最终去重，重复的直接丢弃。

规则：
  * 只新增，不改动现有 g1..gN / hero / 卡片（不动已上线页面的 LCP 图）
  * 每个城市画廊上限 --max（默认 6）张，控制页面体积
  * 幂等：已存在的 -gN.webp 跳过；HTML 里已引用的图不会重复插入

用法：
    python3 tools/cw_expand_galleries.py [--dry-run] [--max N] [--only SLUG ...]
"""
import argparse
import json
import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cw_build_city_images as base

Image.MAX_IMAGE_PIXELS = None

SITE = base.SITE
GAL_SIZE = base.GAL_SIZE
GAL_MAX = base.GAL_MAX
AH = 16
CACHE = os.path.join(SITE, "tools", "img_hash_cache.json")


def bits_of(im):
    g = im.convert("L").resize((AH, AH), Image.LANCZOS)
    px = list(g.getdata())
    avg = sum(px) / len(px)
    b = 0
    for v in px:
        b = (b << 1) | (1 if v > avg else 0)
    return b


def ham(a, b):
    return bin(a ^ b).count("1")


def fast_hash(path):
    """draft 模式：JPEG 直接 1/8 解码，快速拿感知哈希。"""
    try:
        with Image.open(path) as im:
            im.draft("L", (AH, AH))
            return bits_of(im)
    except Exception:
        return None


def crop_hashes(path):
    """把源图按站点三种规格裁切后各算一个哈希，便于与站点成品图同空间比对。

    返回 (gallery, hero, card) 三个哈希；任一为 None 表示该图不可读。
    """
    try:
        with Image.open(path) as im:
            g = bits_of(base.fit_landscape(im, GAL_SIZE))
            h = bits_of(base.fit_landscape(im, base.HERO_SIZE))
            c = bits_of(base.fit_landscape(im, base.CARD_SIZE))
            return g, h, c
    except Exception:
        return None, None, None


def site_hash(path):
    """站点图（已是成品尺寸）的哈希，与新生成的图同一空间，可直接比对。"""
    try:
        with Image.open(path) as im:
            return bits_of(im)
    except Exception:
        return None


def find_grid(h):
    m = re.search(r'<div class="city-gallery-grid">', h)
    if not m:
        return None
    i = m.end()
    depth = 1
    while i < len(h) and depth:
        nxt = h.find("<div", i)
        end = h.find("</div>", i)
        if end == -1:
            break
        if nxt != -1 and nxt < end:
            depth += 1
            i = nxt + 4
        else:
            depth -= 1
            i = end + 6
    return m.start(), i


def alt_prefix(h):
    m = re.search(r'<img src="images/[a-z0-9_]+-g\d+\.webp" alt="([^"]+)"', h)
    if not m:
        return ""
    a = re.sub(r"\s*\d+$", "", m.group(1))
    a = re.sub(r"\s+(photo|cityscape|landmark|local scene|scenery|street scene|view)$", "", a, flags=re.I)
    return a.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max", type=int, default=6)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--sim", type=int, default=10, help="去重的汉明距离阈值")
    args = ap.parse_args()

    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE, encoding="utf-8"))

    cards, page_cn = base.load_site_maps()
    src_idx = base.build_source_index()
    mapping, _ = base.build_mapping(src_idx, cards, page_cn)
    print("源目录条目 %d，映射 slug %d" % (len(src_idx), len(mapping)))

    imgs_dir = os.path.join(SITE, "images")
    card_dir = os.path.join(imgs_dir, "card")
    report = {"added": [], "skipped": [], "failed": [], "dropped_dup": []}

    for slug, base_name in sorted(mapping.items()):
        if args.only and slug not in args.only:
            continue
        page = os.path.join(SITE, slug + ".html")
        if not os.path.exists(page):
            continue
        h = open(page, encoding="utf-8").read()
        if "city-gallery-grid" not in h:
            continue

        used_refs = sorted(set(re.findall(r'images/([a-z0-9_]+-g\d+\.webp)', h)))
        have = len(used_refs)
        if have >= args.max:
            report["skipped"].append((slug, "已有 %d 张" % have))
            continue

        # 站点已用图的哈希（画廊 + hero + 卡片），按各自规格空间取
        gal_hashes = []
        for rel in used_refs:
            x = site_hash(os.path.join(imgs_dir, rel))
            if x is not None:
                gal_hashes.append(x)
        hero_hash = site_hash(os.path.join(imgs_dir, slug + ".webp")) \
            if os.path.exists(os.path.join(imgs_dir, slug + ".webp")) else None
        card_hash = site_hash(os.path.join(card_dir, slug + ".webp")) \
            if os.path.exists(os.path.join(card_dir, slug + ".webp")) else None

        # 源图候选：同城市内去重（源目录大量重复照片），并排除已用过的照片
        files = sorted(src_idx[base_name])
        cands, local = [], []
        for f in files:
            ck = "c:" + f
            if ck not in cache:
                cache[ck] = crop_hashes(f)
            gh, hh, ch = cache[ck]
            if gh is None:
                continue
            if any(ham(gh, y) <= args.sim for y in local):
                continue                     # 源目录内部重复照片
            local.append(gh)
            if any(ham(gh, y) <= args.sim for y in gal_hashes):
                continue                     # 画廊里已经用过
            if hero_hash is not None and hh is not None and ham(hh, hero_hash) <= args.sim:
                continue                     # hero 用的是同一张
            if card_hash is not None and ch is not None and ham(ch, card_hash) <= args.sim:
                continue                     # 卡片用的是同一张
            cands.append(f)
            if len(cands) >= args.max - have:
                break

        if not cands:
            report["skipped"].append((slug, "无新增可用照片"))
            continue

        prefix = alt_prefix(h) or slug
        added, dropped = [], []
        n = have
        for f in cands:
            if n >= args.max:
                break
            n += 1
            out = os.path.join(imgs_dir, "%s-g%d.webp" % (slug, n))
            if os.path.exists(out):
                n -= 1
                continue
            if args.dry_run:
                added.append((n, os.path.basename(f), 0))
                continue
            with Image.open(f) as im:
                gal = base.fit_landscape(im, GAL_SIZE)
                base.save_webp(gal, out, GAL_MAX)
            # 阶段 2：成品空间最终去重
            xh = site_hash(out)
            dup = None
            for y in gal_hashes:
                if xh is not None and ham(xh, y) <= 6:
                    dup = y
                    break
            if dup is not None:
                os.remove(out)
                dropped.append(os.path.basename(f))
                n -= 1
                continue
            gal_hashes.append(xh)
            added.append((n, os.path.basename(f), os.path.getsize(out) // 1024))

        if added and not args.dry_run:
            span = find_grid(h)
            if not span:
                report["failed"].append((slug, "未定位到 city-gallery-grid"))
                continue
            figs = "".join(
                '<figure class="city-gallery-item"><img src="images/%s-g%d.webp" alt="%s photo %d" '
                'loading="lazy" decoding="async" width="900" height="600"></figure>'
                % (slug, nn, prefix, nn) for nn, _, _ in added)
            cut = span[1] - len("</div>")
            h = h[:cut] + figs + h[cut:]
            open(page, "w", encoding="utf-8").write(h)
        if added:
            report["added"].append((slug, added))
        if dropped:
            report["dropped_dup"].append((slug, dropped))

    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f)

    tot = sum(len(a[1]) for a in report["added"])
    print("\n新增 %d 张，涉及 %d 城；跳过 %d；失败 %d；阶段2 判重丢弃 %d" % (
        tot, len(report["added"]), len(report["skipped"]), len(report["failed"]),
        sum(len(d) for _, d in report["dropped_dup"])))
    for slug, items in report["added"][:20]:
        print("   %-14s %s" % (slug, ", ".join("g%d<-%s(%dKB)" % (n, s, kb) for n, s, kb in items)))
    for f in report["failed"]:
        print("  FAIL", f)
    out = os.path.join(SITE, "tools", "gallery_expand_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("报告:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

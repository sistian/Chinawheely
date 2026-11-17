#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性任务：为缺少卡片图的城市批量生成配图（读 /tmp/to_gen.txt 的 slug 列表）。

用法： python3 tools/cw_gen_pending_cards.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "b", os.path.join(HERE, "cw_build_city_images.py"))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

LIST = "/tmp/to_gen.txt"
only = [l.strip() for l in open(LIST, encoding="utf-8") if l.strip()]
print("待生成城市:", len(only))

cards, page_cn = b.load_site_maps()
src_idx = b.build_source_index()
mapping, unresolved = b.build_mapping(src_idx, cards, page_cn)

card_dir = os.path.join(b.SITE, "images", "card")
os.makedirs(card_dir, exist_ok=True)

made, skipped, failed = [], [], []
for slug in only:
    base = mapping.get(slug)
    if not base:
        failed.append((slug, "无源照片"))
        continue
    card_out = os.path.join(card_dir, slug + ".webp")
    hero_out = os.path.join(b.SITE, "images", slug + ".webp")
    gal_out = os.path.join(b.SITE, "images", slug + "-g1.webp")
    if os.path.exists(card_out) and os.path.exists(hero_out):
        skipped.append(slug)
        continue
    files = src_idx[base]
    scored = []
    for f in files:
        try:
            with b.Image.open(f) as im:
                w, h = im.size
        except Exception:
            continue
        scored.append(((1 if w > h else 0, w * h), f))
    if not scored:
        failed.append((slug, "无可读图片"))
        continue
    scored.sort(reverse=True)
    pick = scored[0][1]
    try:
        with b.Image.open(pick) as im:
            b.save_webp(b.fit_landscape(im, b.CARD_SIZE), card_out, b.CARD_MAX)
            csz = os.path.getsize(card_out)
        with b.Image.open(pick) as im:
            b.save_webp(b.fit_landscape(im, b.HERO_SIZE), hero_out, b.HERO_MAX)
            hsz = os.path.getsize(hero_out)
        with b.Image.open(pick) as im:
            b.save_webp(b.fit_landscape(im, b.GAL_SIZE), gal_out, b.GAL_MAX)
            gsz = os.path.getsize(gal_out)
        made.append((slug, base, csz, hsz, gsz))
    except Exception as e:
        failed.append((slug, repr(e)))

print(f"生成 {len(made)}，跳过 {len(skipped)}，失败 {len(failed)}")
for m in made:
    print(f"   {m[0]:12s} card={m[2]//1024}KB hero={m[3]//1024}KB gal={m[4]//1024}KB")
for f in failed:
    print("  FAIL", f)

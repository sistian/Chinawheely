#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为缺口城市里**有源照片**的城市生成 webp（hero / 画廊 / 卡片）
吉安 jian_jx（4 张）、西双版纳 xishuangbanna（1 张）
"""
import os, glob
from PIL import Image, ImageOps

SRC = "/Users/w/Desktop/中国城市图片"
REPO = "/Users/w/Desktop/Chinawheely 10.27"

JOBS = {
    "jian_jx": {"files": ["吉安Jian1.jpg"], "gallery_files": ["吉安Jian2.jpg", "吉安Jian3.jpg", "吉安Jian4.jpg"],
                 "hero": True, "gallery": 3, "card": True},
    "xishuangbanna": {"files": ["西双版纳Xishuangbanna.JPG"], "gallery_files": [],
                      "hero": True, "gallery": 0, "card": True},
}


def save_webp(img, out_path, max_bytes):
    q = 82
    while q >= 30:
        img.save(out_path, "WEBP", quality=q, method=6)
        if os.path.getsize(out_path) <= max_bytes:
            return q
        q -= 8
    return q


def fit(im, size):
    im = ImageOps.exif_transpose(im).convert("RGB")
    return ImageOps.fit(im, size, method=Image.LANCZOS, centering=(0.5, 0.45))


def main():
    for slug, job in JOBS.items():
        files = []
        for pat in job["files"]:
            files += sorted(glob.glob(os.path.join(SRC, pat)))
        if not files:
            print("!! 没找到源图:", slug, job["files"])
            continue
        made = []
        if job.get("hero"):
            im = Image.open(files[0])
            out = os.path.join(REPO, "images", slug + ".webp")
            save_webp(fit(im, (1600, 900)), out, 70 * 1024)
            made.append((out, os.path.getsize(out)))
        for i in range(min(job.get("gallery", 0), len(job.get("gallery_files", [])))):
            im = Image.open(os.path.join(SRC, job["gallery_files"][i]))
            out = os.path.join(REPO, "images", "%s-g%d.webp" % (slug, i + 1))
            save_webp(fit(im, (900, 600)), out, 45 * 1024)
            made.append((out, os.path.getsize(out)))
        if job.get("card"):
            im = Image.open(files[0])
            out = os.path.join(REPO, "images", "card", slug + ".webp")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            save_webp(fit(im, (420, 315)), out, 26 * 1024)
            made.append((out, os.path.getsize(out)))
        for p, s in made:
            print("%-52s %6.1f KB" % (os.path.relpath(p, REPO), s / 1024))


if __name__ == "__main__":
    main()

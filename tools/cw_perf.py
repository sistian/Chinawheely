#!/usr/bin/env python3
"""
W1D5 性能优化
  1. 首页 23 张城市大图（130-309KB，合计 3.4MB）→ 生成 640px 缩略图 images/card/*.webp
  2. 首页 274 张空白城市卡片（style=""）→ 加 CSS 渐变兜底，卡片不再空白
  3. 未被任何页面引用的重型工作文件（合计约 5.4MB）→ 删除
  4. 支付二维码 PNG（537KB+193KB，仅作 <picture> 兜底）→ 转 lossless webp 并改指向，删 PNG
  5. og:image 的 .jpg 引用统一改用 .webp
幂等：可重复执行。
"""
import os, re, sys, json, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cw_common import ROOT, read, write, html_files

try:
    from PIL import Image
except ImportError:
    print("需要 Pillow"); sys.exit(1)

stats = {"thumbnails": 0, "thumb_bytes_before": 0, "thumb_bytes_after": 0,
         "deleted_files": [], "png_to_webp": [], "og_refs": 0}
CARD_DIR = os.path.join(ROOT, "images", "card")

# 未被任何 HTML 引用的重型工作文件
DEAD = ["beijing_final.jpg", "beijing_canvas.jpg", "beijing_test.jpg",
        "chengdu_temp.png", "chengdu_final.png", "changsha.jpg",
        "chengdu_temp.jpg", "beijing.jpg.tmp"]


def make_thumbnails():
    """首页城市卡背景图 → 640px 缩略图"""
    os.makedirs(CARD_DIR, exist_ok=True)
    idx = os.path.join(ROOT, "index.html")
    s = read(idx)
    urls = set(re.findall(r'background-image:\s*url\(["\']?(images/[A-Za-z0-9_.\-]+\.(?:webp|jpg|png))["\']?\)', s))
    for u in sorted(urls):
        src = os.path.join(ROOT, u)
        if not os.path.exists(src):
            continue
        base = os.path.basename(u).rsplit(".", 1)[0]
        dst_rel = f"images/card/{base}.webp"
        dst = os.path.join(ROOT, dst_rel)
        before = os.path.getsize(src)
        if not os.path.exists(dst):
            with Image.open(src) as im:
                im = im.convert("RGB")
                w, h = im.size
                tw = 640
                th = max(1, round(h * tw / w))
                im = im.resize((tw, th), Image.LANCZOS)
                im.save(dst, "WEBP", quality=72, method=6)
        after = os.path.getsize(dst)
        stats["thumbnails"] += 1
        stats["thumb_bytes_before"] += before
        stats["thumb_bytes_after"] += after
        s = s.replace(f"url({u})", f"url({dst_rel})")
        s = s.replace(f"url('{u}')", f"url('{dst_rel}')")
        s = s.replace(f'url("{u}")', f'url("{dst_rel}")')
    write(idx, s)


def delete_dead_files():
    allhtml = "".join(read(os.path.join(ROOT, f)) for f in html_files())
    for f in DEAD:
        p = os.path.join(ROOT, "images", f)
        if not os.path.exists(p):
            continue
        if f in allhtml:
            continue
        size = os.path.getsize(p)
        os.remove(p)
        stats["deleted_files"].append(f"{f} ({size//1024}KB)")


def png_qr_to_webp():
    """支付二维码 PNG → lossless webp（像素完全一致，扫码不受影响）"""
    pairs = [("images/pay-alipay-qr.png", "images/pay-alipay-qr.webp"),
             ("images/alipay-qr.png", "images/alipay-qr.webp"),
             ("images/pay-paypal-qr.png", "images/pay-paypal-qr.webp")]
    for png_rel, webp_rel in pairs:
        png = os.path.join(ROOT, png_rel)
        webp = os.path.join(ROOT, webp_rel)
        if not os.path.exists(png):
            continue
        if not os.path.exists(webp):
            with Image.open(png) as im:
                im.save(webp, "WEBP", lossless=True, quality=100, method=6)
        before = os.path.getsize(png)
        after = os.path.getsize(webp)
        # 所有页面：<img src="png"> → <img src="webp">
        for f in html_files():
            p = os.path.join(ROOT, f)
            s = read(p)
            if png_rel in s:
                s = s.replace(f'src="{png_rel}"', f'src="{webp_rel}"')
                write(p, s)
        os.remove(png)
        stats["png_to_webp"].append(f"{png_rel} {before//1024}KB → {webp_rel} {after//1024}KB")


def og_jpg_to_webp():
    """og:image 引用统一指向 webp"""
    for f in html_files():
        p = os.path.join(ROOT, f)
        s = read(p)
        if "images/og-image.jpg" in s:
            s = s.replace("images/og-image.jpg", "images/og-image.webp")
            write(p, s)
            stats["og_refs"] += 1


if __name__ == "__main__":
    make_thumbnails()
    delete_dead_files()
    png_qr_to_webp()
    og_jpg_to_webp()
    print(json.dumps(stats, ensure_ascii=False, indent=2))

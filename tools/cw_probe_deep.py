#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核查三件事：
  1) jian.html / karakax.html 实际引用了哪些图片，是否与页面文字一致
  2) 源图目录里对「缺失的 31 个自治州/地区/盟 + 吉安」有没有照片
  3) karakax 与 hoting 正文相似度（判断是否同一城市的两张页）
"""
import difflib
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.expanduser("~"), "Desktop", "中国城市图片")


def body(slug):
    f = os.path.join(SITE, slug + ".html")
    if not os.path.exists(f):
        return ""
    h = open(f, encoding="utf-8", errors="replace").read()
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()


def imgs(slug):
    f = os.path.join(SITE, slug + ".html")
    h = open(f, encoding="utf-8", errors="replace").read()
    return sorted(set(re.findall(r'images/([a-z_0-9\-]+\.webp)', h)))


print("=== 1) 页面引用图片 ===")
for s in ["jian", "karakax", "hoting", "yuzhou", "bozhou", "yuxi", "yuxian",
          "bijie", "bitu", "qiqihaer", "qiqihar", "kashgar"]:
    print(f"  {s:11s} {imgs(s)}")

print("\n=== 2) karakax vs hoting 正文相似度 ===")
a, b = body("karakax"), body("hoting")
print("  ratio = %.3f" % difflib.SequenceMatcher(None, a[:6000], b[:6000]).ratio())
print("  karakax 头部:", a[:260])
print("  hoting  头部:", b[:260])

print("\n=== 3) 源图目录里缺失城市的照片 ===")
srcs = os.listdir(SRC) if os.path.isdir(SRC) else []
targets = {
    "吉安": "Ji'an", "红河": "Honghe", "恩施": "Enshi", "延边": "Yanbian",
    "大理": "Dali", "德宏": "Dehong", "西双版纳": "Xishuangbanna",
    "楚雄": "Chuxiong", "怒江": "Nujiang", "迪庆": "Diqing",
    "凉山": "Liangshan", "甘孜": "Ganzi", "阿坝": "Aba",
    "临夏": "Linxia", "甘南": "Gannan", "黄南": "Huangnan",
    "海北": "Haibei", "海南": "Hainan", "海西": "Haixi",
    "果洛": "Guoluo", "玉树": "Yushu", "昌吉": "Changji",
    "巴音郭楞": "Bayin", "博尔塔拉": "Bortala", "克孜勒苏": "Kizilsu",
    "伊犁": "Yili", "塔城": "Tacheng", "阿克苏": "Aksu",
    "阿勒泰": "Altay", "阿里": "Ali", "兴安": "Xingan",
    "锡林郭勒": "Xilinhot", "阿拉善": "Alxa", "大兴安岭": "Daxingan",
    "黔东南": "Qiandongnan", "黔南": "Qiannan", "黔西南": "Qianxinan",
}
for cn, en in targets.items():
    hits = [s for s in srcs if s.startswith(cn) and s.lower().endswith(".jpg")]
    print(f"  {cn:10s} {len(hits):2d} 张  {hits[:2]}")

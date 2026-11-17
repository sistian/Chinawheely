#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收尾修复：
  1. prices.html：删 karakax/yuxian 两个 <details> 块；yuzhou 亳州→禹州、
     fuzhou 福州市→福州、suzhou 苏州市→苏州（data-cn + city-name）
  2. 全站内链重定向：bitu.html→bijie.html、qiqihar.html→qiqihaer.html、
     karakax.html→hoting.html、yuxian.html→yuxi.html（只改 href，不动锚文本）
"""
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REDIR = {"bitu": "bijie", "qiqihar": "qiqihaer", "karakax": "hoting", "yuxian": "yuxi"}


def main():
    # ---------- 1. prices.html ----------
    f = os.path.join(SITE, "prices.html")
    h = open(f, encoding="utf-8").read()
    for s in ["karakax", "yuxian"]:
        pat = re.compile(r'\s*<details class="city" data-slug="%s"[^>]*>.*?</details>' % s, re.S)
        h, n = pat.subn("", h)
        print("prices.html 删块 %-8s %d 处" % (s, n))
    h, a = re.subn(r'(data-slug="yuzhou" data-cn=")亳州(")', r"\g<1>禹州\g<2>", h)
    h, b = re.subn(r'(data-slug="yuzhou"[^>]*>\s*<summary><span class="city-name">)亳州( Yuzhou)', r"\g<1>禹州\g<2>", h)
    h, c = re.subn(r'(data-slug="fuzhou" data-cn=")福州市(")', r"\g<1>福州\g<2>", h)
    h, d = re.subn(r'(data-slug="fuzhou"[^>]*>\s*<summary><span class="city-name">)福州市( Fuzhou)', r"\g<1>福州\g<2>", h)
    h, e = re.subn(r'(data-slug="suzhou" data-cn=")苏州市(")', r"\g<1>苏州\g<2>", h)
    h, g = re.subn(r'(data-slug="suzhou"[^>]*>\s*<summary><span class="city-name">)苏州市( Suzhou)', r"\g<1>苏州\g<2>", h)
    print("prices.html 名字修正: yuzhou %d+%d fuzhou %d+%d suzhou %d+%d" % (a, b, c, d, e, g))
    open(f, "w", encoding="utf-8").write(h)

    # ---------- 2. 全站内链 ----------
    total = 0
    files = 0
    for fn in sorted(os.listdir(SITE)):
        if not fn.endswith(".html"):
            continue
        base = fn[:-5]
        if base in REDIR:
            continue
        p = os.path.join(SITE, fn)
        t = open(p, encoding="utf-8", errors="replace").read()
        t0 = t
        for old, new in REDIR.items():
            t = t.replace('href="%s.html"' % old, 'href="%s.html"' % new)
        if t != t0:
            n = sum(t0.count('href="%s.html"' % o) for o in REDIR)
            total += n
            files += 1
            open(p, "w", encoding="utf-8").write(t)
    print("全站内链改写: %d 处 / %d 个文件" % (total, files))

    # ---------- 3. 验证 ----------
    h = open(f, encoding="utf-8").read()
    for bad in ["karakax", "yuxian", "bitu", "qiqihar"]:
        print("prices.html 残留 %s: %d" % (bad, h.count('"%s.html"' % bad) + h.count('data-slug="%s"' % bad)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

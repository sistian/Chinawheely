#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prices.html 收尾：
  1. 探测城市价格块边界结构
  2. 删 karakax / yuxian 整块
  3. 块内错误中文名修正（亳州→禹州、福州市→福州、苏州市→苏州 仅限标签/标题）
  4. 全站残留扫描：错误中文名 + 错误锚文本
"""
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rd(f):
    return open(os.path.join(SITE, f), encoding="utf-8").read()


def wr(f, h):
    open(os.path.join(SITE, f), "w", encoding="utf-8").write(h)


def main():
    h = rd("prices.html")

    # --- 1. 块结构探测：karakax 的 city-guide-link 往前找块开始标记
    i = h.find('href="karakax.html"')
    print("=== karakax 块前 600 字符 ===")
    print(re.sub(r"\s+", " ", h[i - 600:i]))
    print()
    # 数一下可能的块开始标记
    for pat in ['class="price-card"', 'class="city-price"', "<h3", "price-block", "accordion"]:
        print("   %-22s %d 处" % (pat, h.count(pat)))

    # --- 3. prices.html 内的中文错误名
    for bad, good in [("亳州", "禹州"), ("福州市", "福州"), ("苏州市", "苏州")]:
        for m in re.finditer(bad, h):
            j = m.start()
            print("   prices.html「%s」: %s" % (bad, re.sub(r"\s+", " ", h[max(0, j - 70):j + 70])))

    # --- 4. 全站残留扫描
    print("\n=== 全站残留扫描（bitu/qiqihar/karakax/yuxian 的站内链接）===")
    n = 0
    for f in sorted(os.listdir(SITE)):
        if not f.endswith(".html") or f in ("bitu.html", "qiqihar.html", "karakax.html", "yuxian.html"):
            continue
        t = open(os.path.join(SITE, f), encoding="utf-8", errors="replace").read()
        for s in ["bitu", "qiqihar", "karakax", "yuxian"]:
            for m in re.finditer(r'<a[^>]*href="%s\.html"[^>]*>' % s, t):
                n += 1
                if n <= 20:
                    print("   %-22s -> %s.html" % (f, s))
    print("   合计 %d 处（karakax/yuxian 页内互链暂列其中）" % n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测 karakax/yuxian 页面价格区块的结构与边界。"""
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    for slug in ["karakax", "yuxian"]:
        h = open(os.path.join(SITE, slug + ".html"), encoding="utf-8").read()
        print("=== %s.html (%d bytes) ===" % (slug, len(h)))
        # 找价格相关标记
        for pat in ["From ¥", "pl-head", "pl-title", "price-section", "qb-",
                    "Transparent Price", "id=\"pricing", "section id=\"price"]:
            n = h.count(pat)
            if n:
                print("   %-22s %d 处" % (pat, n))
        # From ¥ 首次出现的上下文
        i = h.find("From ¥")
        if i >= 0:
            print("   From ¥ 上下文: %s" % re.sub(r"\s+", " ", h[max(0, i - 150):i + 60]))
        # 价格 section 的开头
        m = re.search(r'<section[^>]*id="price[^"]*"[^>]*>', h)
        if m:
            j = m.start()
            print("   section#price 开头: %s" % re.sub(r"\s+", " ", h[j:j + 160]))
        else:
            # 找 pl-head 前面的 section 开始
            m = re.search(r'pl-head', h)
            if m:
                j = h.rfind("<section", 0, m.start())
                print("   pl-head 所在 section: %s" % re.sub(r"\s+", " ", h[j:j + 160]))
        # Quote on request 存在吗
        print("   Quote on request: %d 处" % h.count("Quote on request"))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

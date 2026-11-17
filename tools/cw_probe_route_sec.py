#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看 karakax/yuxian 中含 From ¥ 的 route 报价 section 的完整内容。"""
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sections(h):
    out = []
    stack = []
    for m in re.finditer(r"<section\b[^>]*>|</section>", h):
        if m.group(0).startswith("<section"):
            stack.append(m.start())
        else:
            s = stack.pop()
            if not stack:
                out.append((s, m.end()))
    return out


def main():
    for slug in ["karakax", "yuxian"]:
        h = open(os.path.join(SITE, slug + ".html"), encoding="utf-8").read()
        m = re.search(r"From ¥\d", h)
        if not m:
            print("%s: 无 From ¥" % slug)
            continue
        for s, e in sections(h):
            if s <= m.start() < e:
                frag = h[s:e]
                heads = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", frag, re.S)
                print("=== %s.html 报价 section %d 字节 ===" % (slug, e - s))
                print("   开头: %s" % re.sub(r"\s+", " ", h[s:s + 130]))
                print("   标题: %s" % [re.sub(r'<[^>]+>', '', x).strip()[:60] for x in heads[:6]])
                # 该 section 前一个 section 是什么（找区块名）
                allsec = sections(h)
                idx = next(i for i, (a, b) in enumerate(allsec) if a == s)
                if idx > 0:
                    print("   前一个 section 开头: %s" % re.sub(
                        r"\s+", " ", h[allsec[idx - 1][0]:allsec[idx - 1][0] + 100]))
                print("   结尾: %s" % re.sub(r"\s+", " ", h[e - 120:e]))
                print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

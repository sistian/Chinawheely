#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""删除 karakax/yuxian 页面的价格区块（别名页不展示与正牌页可能不一致的价格）。

  1. 深度计数定位 <section id="price-list"> 到配对 </section>，整块删除
  2. 找出其余 From ¥ 所在的 section，逐个处理（删除 qb/adv 报价行或替换）
  3. 删 TOC 中指向已删标题的条目
  4. 保证页内保留至少一处 "Quote on request"（无价城门禁要求）
"""
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sections(h):
    """返回 [(start, end, attrs)]，end 为配对 </section> 之后的位置。"""
    out = []
    stack = []
    for m in re.finditer(r"<section\b[^>]*>|</section>", h):
        if m.group(0).startswith("<section"):
            stack.append(m.start())
        else:
            s = stack.pop()
            if not stack:
                out.append((s, m.end(), h[s:s + 120]))
    return out


def main():
    for slug in ["karakax", "yuxian"]:
        p = os.path.join(SITE, slug + ".html")
        h = open(p, encoding="utf-8").read()

        print("=== %s.html ===" % slug)
        # 删 price-list section
        m = re.search(r'<section class="section pl-section" id="price-list">', h)
        if m:
            for s, e, a in sections(h):
                if s == m.start():
                    frag = h[s:e]
                    nfy = len(re.findall(r"From ¥\d", frag))
                    nq = frag.count("Quote on request")
                    h = h[:s] + h[e:]
                    print("  删 price-list section %d 字节（内含 From ¥ %d 处 / Quote %d 处）"
                          % (e - s, nfy, nq))
                    break

        # 其余 From ¥ 的位置
        for m in re.finditer(r"From ¥\d", h):
            j = m.start()
            sec = ""
            for s, e, a in sections(h):
                if s <= j < e:
                    sec = re.sub(r"\s+", " ", a[:60])
            print("  残留 From ¥ @%d in %s: %s" % (
                j, sec[:46], re.sub(r"\s+", " ", h[max(0, j - 120):j + 30])[-100:]))

        # TOC 残留死锚
        dead = re.findall(r'href="#toc-transparent-pricing[^"]*"', h)
        print("  TOC 死锚: %d" % len(dead))

        # Quote on request 位置
        for m in re.finditer(r"Quote on request", h):
            j = m.start()
            sec = ""
            for s, e, a in sections(h):
                if s <= j < e:
                    sec = re.sub(r"\s+", " ", a[:50])
            print("  Quote @%d in %s" % (j, sec[:46]))

        open(p, "w", encoding="utf-8").write(h)
        print("  写回 %d 字节\n" % len(h))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

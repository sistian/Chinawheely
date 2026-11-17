#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""karakax/yuxian 别名页收尾：
  1. 删除 Popular Routes 报价 section（From ¥ 所在）
  2. 删除 TOC 中指向已删标题的死锚条目
  3. 验证：From ¥=0、Quote on request>=1、section 配对平衡
"""
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
        p = os.path.join(SITE, slug + ".html")
        h = open(p, encoding="utf-8").read()
        n0 = len(h)

        m = re.search(r"From ¥\d", h)
        if m:
            for s, e in sections(h):
                if s <= m.start() < e:
                    h = h[:s] + h[e:]
                    print("%s 删 route 报价 section %d 字节" % (slug, e - s))
                    break

        # TOC 死锚条目（<li><a href="#toc-...">...</a></li>）
        for anchor in re.findall(r'href="#(toc-(?:popular-[^"]*|transparent-pricing[^"]*))"', h):
            pat = re.compile(r'<li[^>]*>\s*<a href="#%s">.*?</a>\s*</li>' % re.escape(anchor), re.S)
            h, n = pat.subn("", h)
            print("%s 删 TOC 条目 %s %d 处" % (slug, anchor, n))
        # 也可能有非 li 包裹的 TOC 链接
        h, n = re.subn(r'<a href="#toc-(?:popular-[^"]*|transparent-pricing[^"]*)">.*?</a>', "", h,
                       flags=re.S)
        if n:
            print("%s 删散落 TOC 链接 %d 处" % (slug, n))

        nfy = len(re.findall(r"From ¥\d", h))
        nq = h.count("Quote on request")
        opens = len(re.findall(r"<section\b", h))
        closes = len(re.findall(r"</section>", h))
        print("%s 结果: From ¥=%d Quote=%d section<%d/>%d %d→%d 字节\n"
              % (slug, nfy, nq, opens, closes, n0, len(h)))
        open(p, "w", encoding="utf-8").write(h)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

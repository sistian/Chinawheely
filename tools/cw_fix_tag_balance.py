#!/usr/bin/env python3
"""
标签闭合机械修复（只动标签，不改任何文案）
  1. "Popular Long-tail Routes" 区块：</section> 提前关闭了 <div class="container">
     和 <div class="section-header">，HTML5 解析器会隐式补闭合，渲染无差；
     这里补上显式 </div>，让源码结构合法。
  2. 同一区块末尾多余的孤立 </section>（Long-tail 区块被多包了一层时产生）。
幂等：可重复执行。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cw_common import ROOT, read, write, html_files

RE_BLOCK = re.compile(
    r"(<!-- Popular Long-tail Routes -->\s*<section\b[^>]*>)(.*?)(</section>\s*)",
    re.S,
)
RE_EXTRA_SECTION = re.compile(r"(</section>\s*){2,}")


def fix_block(m):
    head, body, tail = m.group(1), m.group(2), m.group(3)
    opens = len(re.findall(r"<div\b", body))
    closes = len(re.findall(r"</div>", body))
    missing = opens - closes
    if missing <= 0:
        return m.group(0)
    # 按缩进把缺失的 </div> 补在 </section> 之前
    indent = re.match(r"([ \t]*)", tail).group(1)
    fix = "".join(f"{indent}</div>\n" for _ in range(missing))
    return head + body + fix + tail


def main():
    stats = {"blocks_fixed": 0, "extra_section": 0, "pages": 0}
    for f in html_files():
        p = os.path.join(ROOT, f)
        s = read(p)
        o = s

        s, n = RE_BLOCK.subn(fix_block, s)
        stats["blocks_fixed"] += n

        # Long-tail 区块后紧跟的孤立 </section>：删掉多余的
        s = re.sub(
            r"(<!-- Popular Long-tail Routes -->.*?</section>\s*)</section>",
            r"\1",
            s,
            flags=re.S,
        )

        if s != o:
            write(p, s)
            stats["pages"] += 1

    import json

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

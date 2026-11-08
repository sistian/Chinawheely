#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一「报价 48 小时有效」口径。

背景：
  - 此前只有 bitu.html / qiqihar.html 两个别名页写了「The quote is valid for 48 hours」
  - 其余 341 个城市页的透明价格区 / 无价城 Quote on request 区都没有这句
  - 用户已确认「报价 48 小时有效」是全站统一口径

做法（幂等）：
  A. 有价城：在 pl-section 的 </div>（容器收尾）前插入 <p class="pl-validity">…</p>
  B. 无价城：在 quote 区块的说明段后插入同样的一句
  句子统一为同一句英文，避免两种区块说法不一致。

已存在该句的页面跳过（幂等）。
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VALIDITY_SENTENCE = (
    "The quote is valid for 48 hours, and you can change or cancel free "
    "up to 48 hours before pickup."
)

# 有价城：<p class="pl-validity">…</p>
PL_MARK = 'class="pl-validity"'

# 无价城：<p class="qb-validity">…</p>
QB_MARK = 'class="qb-validity"'


def pl_insert_pattern():
    """有价城：找到 pl-section 内最后的 </div>\n </div> 结构之前的容器收尾。

    实际结构（beijing.html）：
        <section class="section pl-section" id="price-list">
         <div class="container">
          ...
          </div>     <- pl-card 容器结束
         </div>      <- .container 结束
        </section>
    我们在 </section> 之前、.container 结束之后插入是不合法的（section 里插入 p 需要在 container 内）。

    更稳妥：定位 pl-section 段落中最后一个 '</table>\n   </div>' 之后插入，
    但结构多样。改用「在 pl-section 的 </section> 之前插入 <p>」——
    <p> 是 flow content，section 内直接放 <p> 合法。
    """
    return None


def add_validity(html):
    """返回 (新html, 改动说明)"""
    notes = []

    # ---------- A. 有价城 pl-section ----------
    if PL_MARK not in html and 'id="price-list"' in html:
        m = re.search(
            r'(<section[^>]*class="[^"]*pl-section[^"]*"[^>]*id="price-list"[^>]*>)(.*?)(</section>)',
            html, re.S)
        if m:
            body = m.group(2)
            para = (
                '  <p class="pl-validity">%s</p>\n' % VALIDITY_SENTENCE
            )
            new_body = body.rstrip()
            # 保证 </div> 之后紧接 </section> 的结构不被破坏：插到最后一个 </div> 之后
            new_body = new_body + '\n' + para.rstrip('\n') + '\n '
            html = html[:m.start(2)] + new_body + html[m.end(2):]
            notes.append('pl-section')

    # ---------- B. 无价城 quote 区块 ----------
    if QB_MARK not in html and 'Quote on request' in html:
        # 找到 Quote on request 之后最近的一个 </p>，在其后插入
        idx = html.find('Quote on request')
        if idx != -1:
            close = html.find('</p>', idx)
            if close != -1:
                ins = close + len('</p>')
                para = ('\n<p class="qb-validity">%s</p>' % VALIDITY_SENTENCE)
                html = html[:ins] + para + html[ins:]
                notes.append('quote-block')

    return html, notes


def main():
    files = [f for f in os.listdir(ROOT)
             if f.endswith('.html') and not f.startswith('.')]
    changed = 0
    total_notes = {}
    for f in sorted(files):
        path = os.path.join(ROOT, f)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                src = fh.read()
        except Exception as e:
            print('READ FAIL %s: %s' % (f, e))
            continue
        new, notes = add_validity(src)
        if new != src and notes:
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(new)
            changed += 1
            for n in notes:
                total_notes[n] = total_notes.get(n, 0) + 1

    print('扫描 %d 个 html，改动 %d 个' % (len(files), changed))
    print('改动分布：%s' % total_notes)

    # 复查
    both = 0
    onlyone = []
    for f in sorted(files):
        path = os.path.join(ROOT, f)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                s = fh.read()
        except Exception:
            continue
        has_pl = PL_MARK in s
        has_qb = QB_MARK in s
        has_val = VALIDITY_SENTENCE in s
        if has_val and not (has_pl or has_qb):
            both += 1
        if (has_pl or has_qb) and not has_val:
            onlyone.append(f)
    print('含 validity 句但无标记：%d' % both)
    print('有标记但缺句子：%d %s' % (len(onlyone), onlyone[:5]))
    return 0


if __name__ == '__main__':
    sys.exit(main())

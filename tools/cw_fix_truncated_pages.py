#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复两页「尾部整块丢失」。

发现（2026-11-07 审计）：2 个**可索引且在 sitemap 里**的页面尾部被截断：
  - beijing-tea-culture.html：内容停在 page-siblings 里的 </ul>，
                             缺 siblings 容器的 </div></div>、footer、WhatsApp、scripts.js
  - linfen.html：正文结束即 </body>
                 缺 link-hub 内链区块、footer、WhatsApp、scripts.js

成因：历史提交（f2773df5 / d630797f）写这两页时把尾部区块丢了，
     不是本次改动引入的回归（git log 已确认）。

修法：从「结构完好的同族/同省页面」取尾部区块原样搬过来，
      只替换与城市相关的部分（footer-cities / link-hub 同省城市列表）。

用法：python3 tools/cw_fix_truncated_pages.py [--dry-run]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(f):
    with open(os.path.join(ROOT, f), encoding='utf-8', errors='ignore') as fh:
        return fh.read()


def get_province_cities(f):
    """从某页 footer 的 footer-cities 列表取 [(名称, 文件)]

    注意：footer-cities 块内含嵌套 <div class="footer-title">Cities</div>，
    不能用非贪婪 `.*?</div>` 截取整个块（会误吞第一个 </div>）。
    这里只取 <ul class="footer-links">…</ul> 内的 <li>。
    """
    s = read(f)
    i = s.find('<div class="footer-cities"')
    if i < 0:
        return []
    u = s.find('<ul class="footer-links">', i)
    e = s.find('</ul>', u)
    if u < 0 or e < 0:
        return []
    return [(name, href)
            for href, name in re.findall(r'<li><a href="([^"]+)">([^<]+)</a></li>', s[u:e])]


def swap_footer_cities(foot, cities):
    """替换 footer-cities 里的 <ul class="footer-links"> 列表内容"""
    u = foot.find('<ul class="footer-links">')
    e = foot.find('</ul>', u)
    if u < 0 or e < 0:
        return foot
    items = '\n'.join(f'         <li><a href="{h}">{n}</a></li>' for n, h in cities)
    return foot[:u] + '<ul class="footer-links">\n' + items + '\n        ' + foot[e:]


def build_link_hub(province, same_province_cities, self_city=None, popular_items=''):
    """生成城市页的 link-hub 区块（与其它城市页结构一致）"""
    items = '\n'.join(
        f'        <li><a href="{h}"><span class="ln-cn">{cn}</span>'
        f'<span class="ln-en">{cn}</span></a></li>'
        for cn, h in same_province_cities if h != self_city)
    return (
        ' <section class="section-sm link-hub">\n'
        '    <div class="container">\n'
        '      <div class="section-header">\n'
        '        <h2>More China destinations</h2>\n'
        '        <p class="text-lead">Compare routes, published prices and local driver tips '
        'across the cities we cover.</p>\n'
        '      </div>\n'
        '      <div class="link-cols">\n'
        '      <div class="link-col">\n'
        f'        <h3>Other cities in {province}</h3>\n'
        '        <ul class="link-list">\n' + items + '\n'
        '        </ul>\n'
        '      </div>\n'
        '      <div class="link-col">\n'
        '        <h3>Popular destinations</h3>\n'
        '        <ul class="link-list">\n' + popular_items + '\n'
        '        </ul>\n'
        '      </div>\n'
        '      </div>\n'
        '      <p style="text-align:center;margin-top:var(--space-8);">'
        '<a href="cities.html">Browse all 333 cities we serve &rarr;</a></p>\n'
        '    </div>\n'
        '  </section>\n')


def main():
    dry = '--dry-run' in sys.argv
    plan = []

    # ================= 1) beijing-tea-culture.html =================
    # 模板：beijing-day-trips.html（同城同族，尾部结构完好）
    tpl = read('beijing-day-trips.html')
    i_foot = tpl.find('<footer')
    i_body = tpl.find('</body>')
    tpl_footer_plus = tpl[i_foot:i_body]          # footer + scripts
    # 页面末尾的 WhatsApp 悬浮按钮 + modal（在 footer 之前）
    i_fab = tpl.find('<!-- Floating WhatsApp Button -->')
    fab_block = tpl[i_fab:i_foot] if i_fab > 0 else ''
    # siblings 容器的收尾：模板里 </main> 之后到 <footer> 之前
    i_main = tpl.find('</main>')
    tpl_sib_tail = tpl[i_main + len('</main>'):i_foot]   # 含 </div> + page-siblings 整块

    tgt = read('beijing-tea-culture.html')
    # 本页的 page-siblings 已经存在且内容正确（beijing-* 链接），只是缺容器闭合 + footer
    # 本页 </main> 之后是: '\n</div>\n<div class="page-siblings" ...>...'
    a = tgt.find('</main>')
    assert a > 0
    rest = tgt[a + len('</main>'):]
    # rest 以 '\n</div>\n<div class="page-siblings"...' 开头，末尾是 '...</ul>\n</div>\n</div>\n'
    # 找到最后一个 </ul>（siblings 列表结束）
    last_ul = rest.rfind('</ul>')
    assert last_ul > 0, 'beijing-tea-culture: 找不到 siblings </ul>'
    sib_body = rest[:last_ul + len('</ul>')]
    new_tea = (tgt[:a + len('</main>')] + sib_body
               + '\n  </div>\n </div>\n' + fab_block + tpl_footer_plus
               + '</body>\n</html>\n')
    plan.append(('beijing-tea-culture.html', new_tea))

    # ================= 2) linfen.html（山西临汾） =================
    tpl2 = read('taiyuan.html')
    i_foot2 = tpl2.find('<footer')
    i_body2 = tpl2.find('</body>')
    tpl2_footer_plus = tpl2[i_foot2:i_body2]
    i_fab2 = tpl2.find('<!-- Floating WhatsApp Button -->')
    fab2 = tpl2[i_fab2:i_foot2] if i_fab2 > 0 else ''
    sx = get_province_cities('taiyuan.html')
    foot_sx = swap_footer_cities(tpl2_footer_plus, sx)
    # 同省城市列表的英文名：模板里直接取现成的 <li> 块，改名后复用
    m_sx = re.search(r'<div class="footer-cities"[^>]*>(.*?)</div>', tpl2, re.S)
    pop_match = re.search(r'<h3>Popular destinations</h3>\s*<ul class="link-list">(.*?)</ul>',
                           tpl2, re.S)
    popular_items = pop_match.group(1).strip() if pop_match else ''
    hub = build_link_hub('Shanxi', sx, self_city='linfen.html',
                         popular_items=popular_items)

    tgt2 = read('linfen.html')
    b = tgt2.find('</body>')
    body2 = tgt2[:b].rstrip()
    new_linfen = body2 + '\n\n' + hub + fab2 + foot_sx + '</body>\n</html>\n'
    plan.append(('linfen.html', new_linfen))

    for f, content in plan:
        print(f'{f}: 补齐尾部区块（原 {len(read(f))} → {len(content)} 字节）')
        if not dry:
            with open(os.path.join(ROOT, f), 'w', encoding='utf-8') as fh:
                fh.write(content)


if __name__ == '__main__':
    main()

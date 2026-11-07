#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收尾修复：套餐「含多少」的文案与新口径（35 km + 60 min）对齐 + 404 页补联系方式/牌照
同时同步修改生成器，保证以后重跑不会回退
"""
import glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PAGE_FIX = [
    # 城市页 / prices.html 的机场包描述
    ('35&nbsp;km included; beyond that\n    we charge by the minute and the kilometre at the rates shown.',
     '35&nbsp;km and 60&nbsp;minutes included; beyond that\n    we charge by the minute and the kilometre at the rates shown.'),
    ('35&nbsp;km included; beyond that we charge by the minute and the kilometre at the rates shown.',
     '35&nbsp;km and 60&nbsp;minutes included; beyond that we charge by the minute and the kilometre at the rates shown.'),
    ('<th>Beyond 35 km</th>', '<th>Beyond 35 km / 60 min</th>'),
    ('package includes 35 km)', 'package includes 35 km + 60 minutes)'),
    # 预订页服务卡
    ('Airport pickup &middot; 35 km included', 'Airport pickup &middot; 35 km + 60 min included'),
    ('Airport pickup · 35 km included', 'Airport pickup · 35 km + 60 min included'),
    ('Airport pickup &middot; 35 km include', 'Airport pickup &middot; 35 km + 60 min included'),
    # 机场字段提示
    ('Distances beyond the included 35 km are charged at the published per-km rate.',
     'Your package includes 35 km and 60 minutes. Beyond that we charge by the published per-minute and per-km rate.'),
]

# 生成器同步
GEN_FIX = {
    'tools/gen_prices_page.py': [
        ('package includes 35 km)', 'package includes 35 km + 60 minutes)'),
    ],
    'tools/apply_price_showcase.py': [
        ('35&nbsp;km included; beyond that\n    we charge by the minute and the kilometre at the rates shown.',
         '35&nbsp;km and 60&nbsp;minutes included; beyond that\n    we charge by the minute and the kilometre at the rates shown.'),
        ('<th>Beyond 35 km</th>', '<th>Beyond 35 km / 60 min</th>'),
    ],
}


def main():
    n = 0
    for p in sorted(glob.glob('*.html')):
        s = open(p, encoding='utf-8').read()
        o = s
        for a, b in PAGE_FIX:
            if a in s:
                n += s.count(a)
                s = s.replace(a, b)
        if s != o:
            open(p, 'w', encoding='utf-8').write(s)
    print('页面文案修改 %d 处' % n)

    for f, rules in GEN_FIX.items():
        if not os.path.exists(f):
            continue
        s = open(f, encoding='utf-8').read()
        c = 0
        for a, b in rules:
            if a in s:
                c += s.count(a)
                s = s.replace(a, b)
        if c:
            open(f, 'w', encoding='utf-8').write(s)
        print('生成器 %s 修改 %d 处' % (f, c))

    # 404 页补联系方式 + 牌照
    p = '404.html'
    s = open(p, encoding='utf-8').read()
    if 'L-HUB-101603' not in s:
        add = ('<p class="text-small">Chinawheely &middot; Wuhan City Zhierchong Culture and Tourism Co., Ltd. '
               '&middot; Licence L-HUB-101603 &middot; WhatsApp +86 155 2777 1775 &middot; '
               '<a href="mailto:15527771775@qq.com">15527771775@qq.com</a></p>')
        if '</main>' in s:
            s = s.replace('</main>', add + '\n</main>', 1)
        else:
            s = s.replace('</body>', add + '\n</body>', 1)
        open(p, 'w', encoding='utf-8').write(s)
        print('404.html 已补联系方式与牌照号')
    else:
        print('404.html 已有牌照号，跳过')


if __name__ == '__main__':
    main()

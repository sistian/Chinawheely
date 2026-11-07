#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纠正全站三处不实/不完整承诺（幂等，可重复执行）：
  1) 司机英语能力 —— 司机基本不会英语（用翻译软件），线上客服全英文 24/7 代为沟通
  2) 婴儿/儿童座椅 —— 需额外收费（不再写 free / at no extra charge）
  3) WiFi —— 需提前告知，司机开手机热点并共享网络（不再写 free / included）
"""
import glob, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stats = {}


def bump(k, n=1):
    stats[k] = stats.get(k, 0) + n


def sub_re(s, pattern, repl, key, flags=0, expect=None):
    """正则替换；expect=期望命中次数（None 表示不限，0 表示允许无命中）"""
    new, n = re.subn(pattern, repl, s, flags=flags)
    if n:
        bump(key, n)
    elif expect:
        print(f'!! [{key}] 期望 {expect} 处，实际 0')
    return new


def main():
    files = sorted(glob.glob(os.path.join(BASE, '*.html')))
    for path in files:
        fn = os.path.basename(path)
        s = open(path, encoding='utf-8').read()
        orig = s

        # ────────────────────────────────
        # 1) 司机英语 —— 21 城 JSON-LD FAQ
        # ────────────────────────────────
        def _driver_repl(m):
            city = m.group(1)
            return (m.group(0)[:m.start(2) - m.start(0)] +
                    (f'Most of our drivers in {city} are local chauffeurs and do not speak English '
                     f'- they use translation apps to follow your instructions. That is why every '
                     f'Chinawheely booking comes with English-speaking online support available 24/7 '
                     f'on WhatsApp and WeChat: we speak to the driver on your behalf, confirm the route, '
                     f'the price and any special request, and relay everything back to you. '
                     f'You never need to communicate in Chinese with your driver.') +
                    m.group(0)[m.end(2) - m.start(0):])

        s = sub_re(
            s,
            r'("name": "Is the driver English-speaking\?", "acceptedAnswer": \{"@type": "Answer", "text": ")'
            r'All Chinawheely drivers are professional[^"]*?Our drivers in (.*?) are fluent in basic English[^"]*("\})',
            _driver_repl,
            'faq_driver')

        # ────────────────────────────────
        # 2) 儿童座椅 —— 21 城 JSON-LD FAQ（补"额外收费"）
        # ────────────────────────────────
        def _seat_repl(m):
            return (m.group(1) +
                    ('Yes, child seats can be arranged, but they are an extra charge and are not '
                     'included in the quoted fare. Please tell us the age and weight of your child '
                     'when you book and we will confirm the exact price with you before you pay, '
                     'so the seat is added only with your approval.') +
                    m.group(2))

        s = sub_re(
            s,
            r'("name": "Do you offer child seats\?", "acceptedAnswer": \{"@type": "Answer", "text": ")'
            r'(Yes, child seats are available upon request[^"]*?)(")',
            _seat_repl,
            'faq_seat')

        # ────────────────────────────────
        # 3) 儿童座椅"免费"表述 —— help.html / contact.html / 其它
        # ────────────────────────────────
        s = sub_re(
            s,
            r'child seats are available(?: upon request)? at no extra charge',
            "child seats can be arranged at an extra charge - please tell us your child's age and weight and we will confirm the price before you pay",
            'seat_nocharge')

        s = sub_re(
            s,
            r'Child and baby seats are available with 96 hours advance notice\. This includes cleaning and disinfection\. '
            r'Cost: CNY 200 per seat\.',
            'Child and baby seats are available with 96 hours advance notice, at an extra charge (they are not included in the '
            'quoted fare). This includes cleaning and disinfection. Cost: CNY 200 per seat.',
            'seat_notice')

        # ────────────────────────────────
        # 4) WiFi 表述 —— index / services / booking
        # ────────────────────────────────
        s = sub_re(
            s,
            r'Bottled water &amp; WiFi(?! on request)',
            'Bottled water &amp; WiFi on request (driver shares a hotspot)',
            'wifi_bottled')

        s = sub_re(
            s,
            r'Business Ready: WiFi, phone chargers, bottled water',
            'Business Ready: WiFi on request (your driver shares a mobile hotspot), phone chargers, bottled water',
            'wifi_business')

        s = sub_re(
            s,
            r'In-Car WiFi <span class="u-fdaeaff1">\(Free\)</span>',
            'In-Car WiFi <span class="u-fdaeaff1">(On Request)</span>',
            'wifi_badge')

        # ────────────────────────────────
        # 5) booking.html —— 司机英语 / 婴儿座椅 / WiFi 三处卖点
        # ────────────────────────────────
        if fn == 'booking.html':
            s = sub_re(
                s,
                r'<h4>🙋 Professional Driver</h4>\s*<p>[^<]*</p>',
                '<h4>🙋 Professional Driver</h4>\n'
                ' <p>Licensed local chauffeurs who know every airport and hotel route. Most of our drivers do '
                'not speak English - they use translation apps - but our English-speaking support team is on '
                'WhatsApp and WeChat around the clock and talks to the driver for you, so there is no language '
                'barrier at the airport or the hotel.</p>',
                'booking_driver')

            s = sub_re(
                s,
                r'<h4>💺 Free Child Seat & WiFi</h4>\s*<p>[^<]*</p>',
                '<h4>💺 Child Seat (Extra Charge) &amp; WiFi on Request</h4>\n'
                ' <p>Child seats can be arranged at an extra charge - tell us your child\'s age and weight and we '
                'will confirm the exact price before you pay. In-car WiFi is available on request: message us in '
                'advance and your driver will switch on a mobile hotspot and share the network with you.</p>',
                'booking_seat')

            # 新增「三条说明」区块（插在 What's Included 区块之后）
            if 'Good to Know Before You Book' not in s:
                block = """
 <section class="section u-d9410d69">
 <div class="container">
 <div class="section-header">
 <h2>Good to Know Before You Book</h2>
 <div class="divider"></div>
 <p>Three things travellers ask us about most - here is the honest answer.</p>
 </div>
 <div class="grid grid-3 u-dd7b8907">
 <div class="card u-750445f9">
 <h3 class="lvl-h4">🌐 Language - you will never be stuck</h3>
 <p>Our drivers are local professionals and most of them do not speak English; they use translation apps to
 understand your instructions. Our online customer service team speaks English and is available 24/7 on WhatsApp
 and WeChat - we pass your requests to the driver, confirm the route and the price, and translate anything you
 need. You can book, change and pay entirely in English.</p>
 </div>
 <div class="card u-750445f9">
 <h3 class="lvl-h4">🍼 Baby &amp; Child Seats - extra charge</h3>
 <p>Baby and child seats are <strong>not included</strong> in the quoted fare. They are available at an extra
 charge. Tell us the child's age and weight in the form or on WhatsApp and we will send the exact price before
 you pay, so nothing is added without your approval.</p>
 </div>
 <div class="card u-750445f9">
 <h3 class="lvl-h4">📶 WiFi - tell us in advance</h3>
 <p>In-car WiFi is <strong>on request</strong>, not an automatic extra. Message us before pickup and your driver
 will switch on a mobile hotspot and share the network (name and password) with you on arrival. It is a shared
 mobile connection, so coverage and speed depend on the local network.</p>
 </div>
 </div>
 </div>
 </section>
"""
                m = re.search(r'<section class="section u-0886fa1e">', s)
                if m:
                    e1 = s.find('</section>', m.end())
                    e2 = s.find('</section>', e1 + 10)
                    end = e2 + len('</section>')
                    s = s[:end] + '\n' + block + s[end:]
                    bump('booking_new_block', 1)
                else:
                    print('!! booking.html 找不到 What\'s Included 区块锚点')

        if s != orig:
            open(path, 'w', encoding='utf-8').write(s)

    print('改动统计:')
    for k, v in sorted(stats.items()):
        print(f'  {k}: {v}')
    if not stats:
        print('  (无改动 —— 已经修过了)')


if __name__ == '__main__':
    main()

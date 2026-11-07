#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信息对称性统一修复（幂等）
背景：2026-11-07 全站审计发现同一件事在不同页面说法不一致。

统一口径（以 index.html + 332 城市页 + 系统实际 48h 自助改期为准）：
  取消/退款：>48h 全额退 | 24–48h 退 50% | <24h 不退（可提前 4h 免费改期）
  支付方式：只收 PayPal + Alipay（实际无信用卡通道）
  币种：CNY 为主，USD 仅供参考（1 USD = 7.10 CNY）
  免费等待：机场接送最多 60 分钟
  客服时间：8AM–12AM 北京时间，每周 7 天（与全站 footer 一致）
  发票：不承诺发票，改为订单确认邮件 + 最终价格明细
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# ---------------------------------------------------------------- 取消/退款
CANCEL_OLD = [
    # contact.html / help.html（JSON-LD + 可见）
    ('Yes. Full refund for cancellations &gt;24h before pickup. 50% refund for 12-24h. No refund for &lt;12h.',
     'Yes. Full refund for cancellations more than 48 hours before pickup. 50% refund for 24-48 hours. '
     'No refund under 24 hours - but you can reschedule free of charge if you contact us at least 4 hours before pickup.'),
    ('Yes. Full refund for cancellations >24h before pickup. 50% refund for 12-24h. No refund for <12h.',
     'Yes. Full refund for cancellations more than 48 hours before pickup. 50% refund for 24-48 hours. '
     'No refund under 24 hours - but you can reschedule free of charge if you contact us at least 4 hours before pickup.'),
    ('Full refund for cancellations &gt;24h before pickup. 50% refund for 12-24h. No refund for &lt;12h.',
     'Full refund for cancellations more than 48 hours before pickup. 50% refund for 24-48 hours. '
     'No refund under 24 hours - but you can reschedule free of charge if you contact us at least 4 hours before pickup.'),
    ('Full refund for cancellations >24h before pickup. 50% refund for 12-24h. No refund for <12h.',
     'Full refund for cancellations more than 48 hours before pickup. 50% refund for 24-48 hours. '
     'No refund under 24 hours - but you can reschedule free of charge if you contact us at least 4 hours before pickup.'),
    # help.html
    ('You can cancel for free up to 24 hours before your pickup time. Cancellations within 24 hours may be '
     'subject to a partial charge depending on the city and service type.',
     'You can cancel free of charge up to 48 hours before your pickup time. Cancellations 24-48 hours ahead '
     'receive a 50% refund; under 24 hours there is no refund, but you can reschedule free of charge if you '
     'contact us at least 4 hours before pickup.'),
    ('You can cancel for free up to 24 hours before your pickup time.',
     'You can cancel free of charge up to 48 hours before your pickup time.'),
    # terms.html
    ('<strong>More than 24 hours</strong> before pickup: full refund',
     '<strong>More than 48 hours</strong> before pickup: full refund'),
    ('<strong>12-24 hours</strong> before pickup: 50% refund',
     '<strong>24-48 hours</strong> before pickup: 50% refund'),
    ('<strong>Less than 12 hours</strong> before pickup: no refund',
     '<strong>Less than 24 hours</strong> before pickup: no refund (a free reschedule is possible if you '
     'contact us at least 4 hours before pickup)'),
    # cancellation.html 卡片
    ('<h2 class="lvl-h3">&gt;24 Hours</h2>', '<h2 class="lvl-h3">&gt;48 Hours</h2>'),
    ('<h2 class="lvl-h3">>24 Hours</h2>', '<h2 class="lvl-h3">&gt;48 Hours</h2>'),
    ('<h3>12-24 Hours</h3>', '<h3>24-48 Hours</h3>'),
    ('<h3>&lt;12 Hours</h3>', '<h3>&lt;24 Hours</h3>'),
    ('<h3><12 Hours</h3>', '<h3>&lt;24 Hours</h3>'),
    ('<p>No refund</p>', '<p>No refund - free reschedule if you tell us 4 hours ahead</p>'),
]

# ---------------------------------------------------------------- 支付方式
CARD_OLD = [
    ('We accept PayPal, Alipay, and major credit cards. All payments are processed securely.',
     'We accept PayPal and Alipay. All payments are processed securely - no card details are collected on this site.'),
    ('We accept PayPal, Alipay, and major credit cards. Payment is required before service commencement.',
     'We accept PayPal and Alipay. Payment is required before service commencement.'),
    ('We accept PayPal, Alipay, and major credit cards processed through these providers.',
     'We accept PayPal and Alipay, processed directly through these providers.'),
]

# ---------------------------------------------------------------- 币种
CUR_OLD = [
    ('While prices are displayed in USD, we also accept CNY and EUR.',
     'Published prices are in CNY, with USD shown for reference at 1 USD = 7.10 CNY. '
     'You can pay in CNY or USD through PayPal or Alipay.'),
]

# ---------------------------------------------------------------- 客服时间（24/7 → 与 footer 一致）
SUPPORT_OLD = [
    ('available 24/7 on WhatsApp and WeChat',
     'available 7 days a week (8AM-12AM Beijing time) on WhatsApp and WeChat'),
    ('available 24/7', 'available 7 days a week (8AM-12AM Beijing time)'),
    ('and available 24/7', 'and available 7 days a week (8AM-12AM Beijing time)'),
    ('24/7 on WhatsApp', '7 days a week (8AM-12AM Beijing time) on WhatsApp'),
    ('24/7 English-speaking', '7 days a week (8AM-12AM Beijing time) English-speaking'),
    ('English-speaking online support 24/7', 'English-speaking online support 7 days a week (8AM-12AM Beijing time)'),
]

# ---------------------------------------------------------------- 免费等待 60 分钟
WAIT_OLD = [
    ('free airport waiting time &mdash; nothing is added on the day.',
     'free airport waiting time (up to 60 minutes after your flight lands) &mdash; nothing is added on the day.'),
    ('free airport waiting time - nothing is added on the day.',
     'free airport waiting time (up to 60 minutes after your flight lands) - nothing is added on the day.'),
    ('Flight tracking included &mdash; we wait if you\'re delayed, no extra charge.',
     'Flight tracking included &mdash; we wait if you\'re delayed (up to 60 minutes after landing), no extra charge.'),
    ("Flight tracking included — we wait if you're delayed, no extra charge.",
     "Flight tracking included — we wait if you're delayed (up to 60 minutes after landing), no extra charge."),
    ('free airport waiting time.', 'free airport waiting time (up to 60 minutes after landing).'),
    ('free airport waiting time — nothing is added on the day.',
     'free airport waiting time (up to 60 minutes after your flight lands) — nothing is added on the day.'),
]

# ---------------------------------------------------------------- 发票 / 评价
MISC_OLD = [
    ("You'll receive an invoice by email after your ride.",
     "You'll receive your booking confirmation and the final price breakdown by email."),
    ('spoke perfect English, and got me to my hotel in 45 minutes',
     'used a translation app on his phone, and our WhatsApp team translated everything for us on the way '
     'to the hotel - 45 minutes door to door'),
]


def jsonld_valid(html):
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(b.strip())
        except Exception as e:
            return str(e)[:100]
    return None


def main():
    files = sorted(glob.glob('*.html'))
    total = 0
    per_rule = {}
    touched = 0
    for p in files:
        s = open(p, encoding='utf-8').read()
        orig = s
        n = 0
        for rules, tag in ((CANCEL_OLD, 'cancel'), (CARD_OLD, 'card'), (CUR_OLD, 'currency'),
                           (SUPPORT_OLD, 'support'), (WAIT_OLD, 'waiting'), (MISC_OLD, 'misc')):
            for old, new in rules:
                c = s.count(old)
                if c:
                    s = s.replace(old, new)
                    n += c
                    per_rule[tag] = per_rule.get(tag, 0) + c
        if n:
            err = jsonld_valid(s)
            if err:
                print('!! %s JSON-LD 非法：%s —— 已跳过' % (p, err))
                continue
            open(p, 'w', encoding='utf-8').write(s)
            total += n
            touched += 1
    print('修改 %d 处，涉及 %d 个文件' % (total, touched))
    for k, v in sorted(per_rule.items()):
        print('   %-9s %d 处' % (k, v))

    # 复查
    print('\n--- 复查 ---')
    checks = {
        '残留 ">24h/12-24/<12h" 旧口径': r'>24h before pickup|12-24h|>24h before pickup\.',
        '残留 "24 hours before pickup. Cancellations"': r'cancel for free up to 24 hours',
        '残留 "credit card"（应只剩 booking 的 No credit card required）': r'major credit cards',
        '残留 "24/7"': r'24/7',
        '残留 "invoice"': r'invoice by email',
        '残留 "perfect English"': r'perfect English',
        '残留旧等待文案（无 60 分钟）': r'free airport waiting time &mdash; nothing is added',
    }
    for label, pat in checks.items():
        hit = []
        for p in files:
            s = open(p, encoding='utf-8', errors='ignore').read()
            if re.search(pat, s):
                hit.append(p.replace('.html', ''))
        print('   %-52s %d 个页面 %s' % (label, len(hit), (', '.join(hit[:8]) if hit else '')))
    bad = [p for p in files if jsonld_valid(open(p, encoding='utf-8', errors='ignore').read())]
    print('   JSON-LD 非法页面: %d' % len(bad))


if __name__ == '__main__':
    main()

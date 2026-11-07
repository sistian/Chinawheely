#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽取各页面的取消/退款/等待/支付政策原文，逐页对比"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

FILES = ['booking.html', 'index.html', 'help.html', 'contact.html', 'services.html',
         'cancellation.html', 'terms.html', 'about.html', 'faq.html', 'prices.html',
         'manage-order.html', 'thank-you.html', 'airport-transfer.html', 'city-charter.html',
         'bitu.html', 'qiqihar.html', 'beijing.html', 'shanghai.html']

KEYS = {
    '取消': r'[^\n]{0,220}?(?:cancel|refund)[^\n]{0,220}',
    '免费等待': r'[^\n]{0,200}?wait(?:ing)?[^.\n]{0,140}',
    '支付': r'[^\n]{0,160}?(?:PayPal|Alipay)[^\n]{0,120}',
}


def text_of(f):
    s = open(f, encoding='utf-8', errors='ignore').read()
    s = re.sub(r'<script.*?</script>', ' ', s, flags=re.S)
    s = re.sub(r'<style.*?</style>', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', '\n', s)
    s = s.replace('&mdash;', '—').replace('&nbsp;', ' ').replace('&amp;', '&')
    s = s.replace('&#39;', "'").replace('&quot;', '"')
    lines = [re.sub(r'\s+', ' ', l).strip() for l in s.split('\n')]
    return [l for l in lines if l]


for topic, pat in KEYS.items():
    print('\n' + '=' * 90)
    print('主题：' + topic)
    print('=' * 90)
    for f in FILES:
        if not os.path.exists(f):
            continue
        lines = text_of(f)
        hits = []
        for i, l in enumerate(lines):
            if re.search(pat, l, re.I) and len(l) > 25:
                hits.append(l)
        if not hits:
            continue
        print('\n--- ' + f + ' ---')
        seen = set()
        for h in hits[:4]:
            if h in seen:
                continue
            seen.add(h)
            print('   • ' + h[:250])

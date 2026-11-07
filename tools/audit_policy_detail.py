#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取各页关键政策段落的完整原文（用于人工判定冲突）"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def plain(f):
    s = open(f, encoding='utf-8', errors='ignore').read()
    s = re.sub(r'<script.*?</script>', ' ', s, flags=re.S)
    s = re.sub(r'<style.*?</style>', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', '\n', s)
    for a, b in (('&mdash;', '—'), ('&nbsp;', ' '), ('&amp;', '&'), ('&#39;', "'"),
                 ('&quot;', '"'), ('&yen;', '¥'), ('&lt;', '<'), ('&gt;', '>')):
        s = s.replace(a, b)
    lines = [re.sub(r'\s+', ' ', l).strip() for l in s.split('\n')]
    return [l for l in lines if l]


def show(f, pats, before=0, after=6):
    if not os.path.exists(f):
        return
    lines = plain(f)
    print('\n' + '=' * 88)
    print('### ' + f)
    print('=' * 88)
    for p in pats:
        for i, l in enumerate(lines):
            if re.search(p, l, re.I):
                print('  [' + p[:26] + '] ' + l[:400])
                for j in range(i + 1, min(i + 1 + after, len(lines))):
                    if len(lines[j]) > 8:
                        print('        ↳ ' + lines[j][:260])
                break


CANCEL = [r'cancellation policy', r'how do refunds work', r'refund policy', r'cancel my booking',
          r'full refund', r'48 hours before pickup']
CARD = [r'credit card', r'We accept PayPal']
VALID = [r'quote is valid', r'valid for 48', r'price is valid']
REPLY = [r'within 2 hours', r'within 10 minutes', r'24/7', r'respond within', r'reply within']

for f in ['cancellation.html', 'terms.html', 'help.html', 'contact.html', 'index.html',
          'booking.html', 'services.html', 'thank-you.html', 'faq.html', 'about.html']:
    show(f, CANCEL, after=5)
for f in ['booking.html', 'help.html', 'contact.html', 'terms.html', 'index.html', 'thank-you.html']:
    show(f, CARD, after=2)
for f in ['index.html', 'booking.html', 'help.html', 'contact.html', 'services.html', 'terms.html']:
    show(f, VALID, after=2)
for f in ['index.html', 'booking.html', 'help.html', 'contact.html', 'services.html', 'cancellation.html']:
    show(f, REPLY, after=1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信息对称性审计：扫描全站关键承诺/数字，跨页面聚类，找说法不一致的地方
输出：每个主题下的不同表述 + 出现位置
"""
import glob, json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

htmls = sorted(glob.glob('*.html'))

# ---------- 主题 1：免费/包含/无需付费 类承诺 ----------
FREE_PATTERNS = [
    r'[Ff]ree\b[^<>"]{0,70}',
    r'no extra charge[^<>"]{0,50}',
    r'at no cost[^<>"]{0,40}',
    r'complimentary[^<>"]{0,50}',
    r'included in (?:the |your )?(?:fare|price|package|booking|quote)[^<>"]{0,50}',
]

# ---------- 主题 2：里程/时长口径 ----------
KM_PATTERNS = [
    r'\b\d{1,4}\s?km\b[^<>"]{0,45}',
]

# ---------- 主题 3：回复/响应时间承诺 ----------
TIME_PATTERNS = [
    r'(?:within|in|under)\s+\d+\s*(?:hour|minute|min|hour|day|working day)s?[^<>"]{0,45}',
    r'\d+\s*(?:hours?|minutes?|business days?)\s*(?:reply|response|respond)[^<>"]{0,30}',
]

# ---------- 主题 4：退款/取消 ----------
CANCEL_PATTERNS = [
    r'refund[^<>"]{0,70}',
    r'cancel[^<>"]{0,70}',
    r'no-show[^<>"]{0,40}',
    r'deposit[^<>"]{0,50}',
    r'pay (?:the )?(?:remaining|balance)[^<>"]{0,50}',
]

# ---------- 主题 5：等待/免费等待 ----------
WAIT_PATTERNS = [
    r'wait[^<>"]{0,80}',
]

# ---------- 主题 6：司机英语/客服 ----------
LANG_PATTERNS = [
    r'English[- ]speaking[^<>"]{0,70}',
    r'speak English[^<>"]{0,60}',
    r'fluent[^<>"]{0,60}',
    r'24/7[^<>"]{0,60}',
]

# ---------- 主题 7：支付方式 ----------
PAY_PATTERNS = [
    r'(?:PayPal|Alipay|WeChat Pay|credit card|Credit Card|UnionPay|bank transfer)[^<>"]{0,50}',
]


def scan(patterns, label, min_len=8, top=25):
    buckets = collections.defaultdict(list)
    for f in htmls:
        s = open(f, encoding='utf-8', errors='ignore').read()
        for pat in patterns:
            for m in re.finditer(pat, s):
                t = re.sub(r'\s+', ' ', m.group(0)).strip()
                if len(t) < min_len:
                    continue
                buckets[t].append(f)
    print('\n' + '=' * 78)
    print('主题：' + label + '  （去重表述数 ' + str(len(buckets)) + '）')
    print('=' * 78)
    rows = sorted(buckets.items(), key=lambda kv: -len(kv[1]))
    for t, files in rows[:top]:
        uniq = sorted(set(files))
        print('  [' + str(len(uniq)) + ' 页] ' + t[:110])
        if len(uniq) <= 6:
            print('        → ' + ', '.join(x.replace('.html', '') for x in uniq))
    return buckets


scan(FREE_PATTERNS, '免费/无需额外付费 类承诺')
scan(CANCEL_PATTERNS, '退款 / 取消 / 预付 定金')
scan(WAIT_PATTERNS, '等待（含免费等待）')
scan(LANG_PATTERNS, '司机英语 / 客服响应')
scan(PAY_PATTERNS, '支付方式')
scan(TIME_PATTERNS, '响应时间承诺')
scan(KM_PATTERNS, '里程数字', top=20)

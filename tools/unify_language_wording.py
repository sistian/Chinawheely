#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一 help/index/services 的「司机英语」口径（幂等）：
  司机大多不会英语（用手机翻译软件）→ 订单自带 24/7 真人英语客服（WhatsApp/WeChat）代为沟通
  （原文说 "free Online English Translation Assistant"，容易被误解成机器翻译工具）
"""
import glob, json, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAIRS = [
    # JSON-LD（help/services/index 三处，尾部句子各不相同 → 只替换稳定的引导句）
    ("While they may not speak English fluently, every booking includes a dedicated online human "
     "translation assistant",
     "Most of them do not speak English - they use translation apps on their phone to follow your "
     "instructions. Every booking comes with our English-speaking customer service team (real people, "
     "available 24/7) who speak to the driver on your behalf"),

    # 可见 FAQ（help 的 wording）
    ("Our drivers are professional but not all fluent in English; they use translation apps for daily "
     "communication.",
     "Our drivers are local professionals and most of them do not speak English; they use translation apps "
     "on their phone to follow your instructions."),

    # 可见 FAQ（index / services 的 wording）
    ("Our drivers are professional and experienced, but they are not all fluent English speakers. For "
     "everyday pickup and route communication, they use translation apps and body language.",
     "Our drivers are professional and experienced local chauffeurs, but most of them do not speak English. "
     "For everyday pickup and route communication they use translation apps on their phone and body language."),

    ("every booking includes a free Online English Translation Assistant",
     "every booking includes our English-speaking online customer service team - real people, available "
     "24/7 on WhatsApp and WeChat"),

    ("Every booking includes our free Online English Translation Assistant.",
     "Every booking includes our English-speaking online customer service team - real people, available "
     "24/7 on WhatsApp and WeChat."),
]


def html_valid(html):
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(b.strip())
        except Exception as e:
            return f'JSON-LD 非法: {str(e)[:100]}'
    return None


def main():
    files = sorted(glob.glob(os.path.join(BASE, '*.html')))
    total = 0
    touched = 0
    for p in files:
        s = open(p, encoding='utf-8').read()
        orig = s
        n = 0
        for old, new in PAIRS:
            c = s.count(old)
            if c:
                s = s.replace(old, new)
                n += c
        if n:
            err = html_valid(s)
            if err:
                print(f'!! {os.path.basename(p)} {err} —— 已跳过')
                continue
            open(p, 'w', encoding='utf-8').write(s)
            total += n
            touched += 1
    print(f'统一口径 {total} 处（{touched} 个文件）')

    # 复查
    left = 0
    for p in files:
        s = open(p, encoding='utf-8').read()
        if 'may not speak English fluently' in s or 'free Online English Translation Assistant' in s:
            left += 1
            print('  残留:', os.path.basename(p))
    print(f'复查：残留旧口径文件 {left} 个')


if __name__ == '__main__':
    main()

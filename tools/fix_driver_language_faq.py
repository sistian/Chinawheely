#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复「司机英语」FAQ 的所有格式变体（幂等）：
  - 无论 JSON-LD 是紧凑格式还是 pretty-print 格式，都能定位到
  - 顺带修掉上一版替换残留的旧尾巴（"... with your driver. are fluent in basic English ..."）
统一答案：司机基本不英语（用翻译软件）+ 线上客服全英文 24/7 代为沟通
"""
import glob, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

QUESTION = 'Is the driver English-speaking?'


def new_answer(city):
    c = city.strip()
    return (f'Most of our drivers in {c} are local chauffeurs and do not speak English - they use '
            f'translation apps to follow your instructions. That is why every Chinawheely booking comes '
            f'with English-speaking online support available 24/7 on WhatsApp and WeChat: we speak to the '
            f'driver on your behalf, confirm the route, the price and any special request, and relay '
            f'everything back to you. You never need to communicate in Chinese with your driver.')


def fix_text_value(text_value):
    """text_value 是 JSON 里 "text": "..." 的值（不含引号）→ 返回修复后的值"""
    # 已被正确替换（且无旧尾巴）→ 不动
    if 'do not speak English' in text_value and 'are fluent in basic English' not in text_value:
        return text_value, False
    m = re.search(r'Our drivers in (.+?) are fluent in basic English', text_value)
    if not m:
        return text_value, False
    city = m.group(1)
    return new_answer(city), True


def fix_file(path):
    s = open(path, encoding='utf-8').read()
    orig = s
    n = 0
    while True:
        i = s.find(f'"{QUESTION}"')
        if i < 0:
            break
        # 往后找 "text": "  （允许换行/空格）
        m = re.search(r'"text"\s*:\s*"', s[i:i + 800])
        if not m:
            break
        vstart = i + m.end()
        # 值结束：下一个未转义的引号
        j = vstart
        while j < len(s):
            if s[j] == '\\':
                j += 2
                continue
            if s[j] == '"':
                break
            j += 1
        value = s[vstart:j]
        newv, changed = fix_text_value(value)
        if changed:
            s = s[:vstart] + newv + s[j:]
            n += 1
        else:
            # 已修好 → 检查是否还有旧尾巴残留
            if 'do not speak English' in value and 'are fluent in basic English' in value:
                # 尾部残留：删掉 " are fluent in basic English ... needs." 部分
                k = value.find(' are fluent in basic English')
                s = s[:vstart] + value[:k].rstrip() + s[j:]
                n += 1
            else:
                break
    if s != orig:
        open(path, 'w', encoding='utf-8').write(s)
    return n


def main():
    files = sorted(glob.glob(os.path.join(BASE, '*.html')))
    total = 0
    touched = 0
    for p in files:
        n = fix_file(p)
        if n:
            touched += 1
            total += n
    print(f'修复 {total} 处（{touched} 个文件）')
    # 复查
    left = 0
    for p in files:
        s = open(p, encoding='utf-8').read()
        if 'are fluent in basic English' in s:
            left += 1
    print(f'复查：仍含 "are fluent in basic English" 的文件 {left} 个')


if __name__ == '__main__':
    main()

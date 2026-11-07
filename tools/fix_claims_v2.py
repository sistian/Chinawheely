#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一修复「司机英语」与「儿童座椅收费」FAQ —— 格式无关 + JSON-LD 合法性校验（幂等）

要点：
  * 用「问题名 → 后续 "text": " → 值边界（尊重转义）」定位，不依赖紧凑/漂亮格式
  * 整段替换值，而不是在旧值上拼接（上一版就是在拼接时把整段前缀当成了城市名，写坏了 JSON）
  * 每次改完都对该文件所有 JSON-LD 做 json.loads 校验，失败立刻回滚该文件并报错
"""
import glob, json, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DRIVER_Q = 'Is the driver English-speaking?'
SEAT_Q = 'Do you offer child seats?'


def new_driver_answer(city):
    c = city.strip()
    return (f'Most of our drivers in {c} are local chauffeurs and do not speak English - they use '
            f'translation apps to follow your instructions. That is why every Chinawheely booking comes '
            f'with English-speaking online support available 24/7 on WhatsApp and WeChat: we speak to the '
            f'driver on your behalf, confirm the route, the price and any special request, and relay '
            f'everything back to you. You never need to communicate in Chinese with your driver.')


NEW_SEAT_ANSWER = ("Yes, child seats can be arranged, but they are an extra charge and are not included "
                    "in the quoted fare. Please tell us the age and weight of your child when you book and "
                    "we will confirm the exact price with you before you pay, so the seat is added only "
                    "with your approval.")


def jsonld_blocks(html):
    return re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)


def html_valid(html):
    """校验所有 JSON-LD 块可解析"""
    for b in jsonld_blocks(html):
        try:
            json.loads(b.strip())
        except Exception as e:
            return f'JSON-LD 非法: {str(e)[:120]} | 片段: {b.strip()[:120]}'
    return None


def find_text_value(s, question, span=1500):
    """返回 (value_start, value_end) —— 问题对应的 JSON-LD answer 文本值区间"""
    i = s.find(f'"{question}"')
    if i < 0:
        return None
    m = re.search(r'"text"\s*:\s*"', s[i:i + span])
    if not m:
        return None
    vstart = i + m.end()
    j = vstart
    while j < len(s):
        if s[j] == '\\':
            j += 2
            continue
        if s[j] == '"':
            return vstart, j
        j += 1
    return None


def fix_driver(s):
    rng = find_text_value(s, DRIVER_Q)
    if not rng:
        return s, 0
    vstart, vend = rng
    value = s[vstart:vend]
    if 'do not speak English' in value and 'are fluent in basic English' not in value:
        return s, 0                       # 已修好
    m = re.search(r'Our drivers in (.+?) are fluent in basic English', value)
    if not m:
        return s, 0
    new = new_driver_answer(m.group(1))
    return s[:vstart] + new + s[vend:], 1


def fix_seat(s):
    rng = find_text_value(s, SEAT_Q)
    if not rng:
        return s, 0
    vstart, vend = rng
    value = s[vstart:vend]
    if 'extra charge' in value:
        return s, 0
    if 'child seats' not in value.lower():
        return s, 0
    return s[:vstart] + NEW_SEAT_ANSWER + s[vend:], 1


def main():
    files = sorted(glob.glob(os.path.join(BASE, '*.html')))
    nd = ns = 0
    bad = []
    for p in files:
        s = open(p, encoding='utf-8').read()
        orig = s
        s, a = fix_driver(s)
        s, b = fix_seat(s)
        if a or b:
            err = html_valid(s)
            if err:
                print(f'!! {os.path.basename(p)} {err}')
                bad.append(p)
                continue
            open(p, 'w', encoding='utf-8').write(s)
            nd += a
            ns += b
    print(f'司机 FAQ 修复 {nd} 处；儿童座椅 FAQ 修复 {ns} 处；JSON-LD 非法文件 {len(bad)} 个')

    # 复查
    left_d = left_s = 0
    for p in files:
        s = open(p, encoding='utf-8').read()
        if 'are fluent in basic English' in s:
            left_d += 1
        if html_valid(s):
            left_s += 1
    print(f'复查：仍含旧司机表述 {left_d} 个文件；JSON-LD 非法 {left_s} 个文件')
    return 1 if (bad or left_d or left_s) else 0


if __name__ == '__main__':
    sys.exit(main())

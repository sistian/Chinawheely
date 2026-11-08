#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上生效验证：轮询 GitHub Pages 发布（最多 5 分钟）"""
import re, time, urllib.request, urllib.error

BASE = 'https://www.chinawheely.com'


def get(path, timeout=25):
    req = urllib.request.Request(BASE + path, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return 0, str(e)[:80]


CHECKS = [
    ('contact.html', 'e.preventDefault();', '联系表单限流/邮箱校验'),
    ('contact.html', 'e.preventDefault;', None),   # 反向：不应存在缺括号写法
    ('index.html', '<a class="nav-logo" href="index.html">', '首页 logo 链接'),
    ('index.html', 'href="#"', None),              # 反向：不应有空 href
    ('juancheng.html', 'booking.html?city=Juancheng', '济宁/巨城按钮'),
    ('chongqing.html', 'chongqing-tea-culture.html', '茶文化卡片链接'),
    ('xian.html', 'id="best-time-guide"', '重复 id 修复'),
    ('404.html', '<main>', '404 页 main 地标'),
]


def scan():
    res = []
    for path, needle, desc in CHECKS:
        code, body = get('/' + path)
        if code != 200:
            res.append((path, desc, 'HTTP %s' % code, False))
            continue
        ok = (needle in body)
        if desc is None:      # 反向检查
            ok = not ok
            desc = '不应出现: ' + needle
        res.append((path, desc, 'OK' if ok else '未生效', ok))
    return res


print('轮询线上发布状态…')
deadline = time.time() + 300
last = None
while time.time() < deadline:
    last = scan()
    if all(r[3] for r in last):
        break
    time.sleep(20)

print('\n=== 线上验证结果 ===')
allok = True
for path, desc, st, ok in last:
    print('  %-16s %-30s %s' % (path, desc, '✅ ' + st if ok else '❌ ' + st))
    allok = allok and ok

print('\n=== 调试残留检查（线上随机页）===')
for p in ['index.html', 'booking.html', 'contact.html', '404.html', 'manage-order.html']:
    code, body = get('/' + p)
    leak = ('window.__errs' in body) or ('o.formAction' in body) or ('document.title=JSON.stringify' in body)
    print('  %-20s HTTP %s  残留: %s' % (p, code, '❌ 有' if leak else '✅ 无'))
    allok = allok and not leak

print('\n结论:', '全部通过 ✅' if allok else '仍有未生效项 ❌')

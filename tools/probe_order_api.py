#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查单/改期接口的越权与注入探测（只读 GET + 拒绝性 PATCH）"""
import json, urllib.request, urllib.error, urllib.parse

BASE = 'https://api.chinawheely.com/api/order'


def call(method, qs=None, body=None, label=''):
    url = BASE + (('?' + urllib.parse.urlencode(qs)) if qs else '')
    data = None
    if body is not None:
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Origin', 'https://www.chinawheely.com')
    req.add_header('Content-Type', 'application/json')
    try:
        r = urllib.request.urlopen(req, timeout=25)
        code, txt = r.status, r.read().decode('utf-8', 'ignore')[:160]
    except urllib.error.HTTPError as e:
        code, txt = e.code, e.read().decode('utf-8', 'ignore')[:160]
    except Exception as e:
        code, txt = 'ERR', str(e)[:100]
    print('  %-46s → %-4s %s' % (label, code, txt.replace('\n', ' ')[:110]))
    return code


print('=== GET 查单（各种异常 ref/token）===')
call('GET', {'ref': 'CWO-20260101-AAAAAAAA', 'token': 'wrong'}, label='不存在订单 + 错 token')
call('GET', {'ref': 'CWO-20260101-AAAAAAAA', 'token': ''}, label='不存在订单 + 空 token')
call('GET', {'ref': 'not-a-ref', 'token': 'x'}, label='ref 格式非法')
call('GET', {}, label='无参数')
call('GET', {'ref': "' OR '1'='1", 'token': "' OR '1'='1"}, label='SQL 注入式 ref')
call('GET', {'ref': '../../etc/passwd', 'token': 'x'}, label='路径穿越 ref')
call('GET', {'ref': 'CWO-20260101-AAAAAAAA', 'token': "' OR '1'='1"}, label='SQL 注入式 token')

print('\n=== PATCH 改期（拒绝性）===')
call('PATCH', None, {'ref': 'CWO-20260101-AAAAAAAA', 'token': 'wrong',
                      'pickup_date': '2026-12-01', 'pickup_time': '10:00'},
     label='错 token 改期')
call('PATCH', None, {'ref': 'CWO-20260101-AAAAAAAA', 'token': 'x'}, label='缺日期改期')
call('PATCH', None, {'ref': 'CWO-20260101-AAAAAAAA', 'token': 'x',
                     'pickup_date': 'not-a-date', 'pickup_time': '99:99'},
     label='非法日期时间')

print('\n=== 管理后台鉴权 ===')
for p in ['/api/admin/orders', '/api/admin/login']:
    url = 'https://api.chinawheely.com' + p
    req = urllib.request.Request(url, data=b'{}', method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        r = urllib.request.urlopen(req, timeout=20)
        print('  POST %-26s → %s %s' % (p, r.status, r.read().decode('utf-8', 'ignore')[:100].replace('\n', ' ')))
    except urllib.error.HTTPError as e:
        print('  POST %-26s → %s %s' % (p, e.code, e.read().decode('utf-8', 'ignore')[:100].replace('\n', ' ')))
    except Exception as e:
        print('  POST %-26s → ERR %s' % (p, str(e)[:80]))
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, method='GET'), timeout=20)
        print('  GET  %-26s → %s %s' % (p, r.status, r.read().decode('utf-8', 'ignore')[:100].replace('\n', ' ')))
    except urllib.error.HTTPError as e:
        print('  GET  %-26s → %s %s' % (p, e.code, e.read().decode('utf-8', 'ignore')[:100].replace('\n', ' ')))
    except Exception as e:
        print('  GET  %-26s → ERR %s' % (p, str(e)[:80]))

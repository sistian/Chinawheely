#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上 API 安全探测：只触发拒绝分支，不创建真实线索、不发邮件"""
import json, time, urllib.request, urllib.error

API = 'https://api.chinawheely.com/api/contact'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36'


def post(body, origin='https://www.chinawheely.com', label=''):
    data = urllib.parse.urlencode(body).encode()
    req = urllib.request.Request(API, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    req.add_header('User-Agent', UA)
    req.add_header('Origin', origin)
    req.add_header('Referer', origin + '/contact.html')
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=30)
        code, body_txt, loc = r.status, r.read().decode('utf-8', 'ignore')[:200], r.headers.get('Location')
    except urllib.error.HTTPError as e:
        code, body_txt, loc = e.code, e.read().decode('utf-8', 'ignore')[:200], e.headers.get('Location')
    except Exception as e:
        code, body_txt, loc = 'ERR', str(e)[:150], None
    dt = int((time.time() - t0) * 1000)
    print('  %-34s → %s %sms %s' % (label, code, dt, (loc or body_txt).replace('\n', ' ')[:90]))
    return code


import urllib.parse  # noqa

print('=== 拒绝分支（不应创建线索、不应发邮件）===')
post({'firstName': 'Spam', 'lastName': 'Bot', 'email': 'spam@example.com',
      'message': 'spam', 'website': 'http://spam'}, label='honeypot 填值')
post({'firstName': 'Bad', 'lastName': 'Mail', 'email': 'not-an-email',
      'message': 'x'}, label='非法 email')
post({'firstName': 'X', 'lastName': 'Y', 'email': '', 'message': 'x'}, label='空 email')
post({}, label='全空')
post({'firstName': 'A', 'lastName': 'B', 'email': 'a@b.co', 'message': 'x',
      '_t': str(int(time.time() * 1000))}, label='填写耗时 0 秒（应 400）')
post({'firstName': 'A', 'lastName': 'B', 'email': 'a@b.co', 'message': 'x',
      '_t': str(int((time.time() - 30) * 1000))}, label='填写耗时 30 秒（应通过→302，但会建线索）',
      ) if False else None

print('\n=== CORS 行为 ===')
post({'firstName': 'X', 'lastName': 'Y', 'email': 'a@b.co', 'message': 'x',
      'website': 'z'}, origin='https://evil.example.com', label='恶意 Origin + honeypot')

print('\n=== OPTIONS 预检 ===')
req = urllib.request.Request(API, method='OPTIONS')
req.add_header('Origin', 'https://www.chinawheely.com')
req.add_header('Access-Control-Request-Method', 'POST')
try:
    r = urllib.request.urlopen(req, timeout=20)
    print('  OPTIONS →', r.status, dict((k, v) for k, v in r.headers.items()
                                         if k.lower() in ('allow', 'access-control-allow-origin',
                                                          'access-control-allow-methods')))
except urllib.error.HTTPError as e:
    print('  OPTIONS →', e.code)

print('\n=== 其它端点存活检查 ===')
for p in ['/api/quote', '/api/booking', '/api/manage-order', '/api/order']:
    try:
        req = urllib.request.Request('https://api.chinawheely.com' + p,
                                     data=b'{}', method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Origin', 'https://www.chinawheely.com')
        r = urllib.request.urlopen(req, timeout=25)
        print('  POST %-22s → %s' % (p, r.status))
    except urllib.error.HTTPError as e:
        print('  POST %-22s → %s %s' % (p, e.code, e.read().decode('utf-8', 'ignore')[:70].replace('\n', ' ')))
    except Exception as e:
        print('  POST %-22s → ERR %s' % (p, str(e)[:70]))

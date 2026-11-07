#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
站点"暗病"体检 —— 静态部分
检查项：
 1. 资源引用失效（img/script/link/iframe 的本地路径）
 2. 内部链接死链（指向不存在的 .html / 目录 / 锚点）
 3. 重复 id、空 alt、缺 h1、缺 meta description
 4. 表单字段 ↔ 后端接收字段不匹配
 5. 外链资源可达性（仅报告，不请求）
 6. 体积异常的大文件
"""
import glob, json, os, re, collections, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

htmls = sorted(glob.glob('*.html'))
jsfiles = sorted(glob.glob('js/*.js')) + sorted(glob.glob('api/*.js')) + sorted(glob.glob('api/_lib/*.js'))

issues = collections.defaultdict(list)

# ---------------------------------------------------------------- 1) 资源引用
RES = re.compile(r'''(?:src|href)\s*=\s*["']([^"'#?][^"']*)["']''', re.I)
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    for m in RES.finditer(s):
        u = m.group(1).strip()
        if not u or u.startswith(('http://', 'https://', '//', 'mailto:', 'tel:', 'data:', 'javascript:')):
            continue
        path = u.split('#')[0].split('?')[0]
        if not path:
            continue
        if not os.path.exists(path):
            issues['资源失效'].append((f, u))

# ---------------------------------------------------------------- 2) 内部链接
ids_by_file = {}
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    ids_by_file[f] = set(re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', s))

for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'href\s*=\s*["\']([^"\']+)["\']', s, re.I):
        u = m.group(1).strip()
        if u.startswith(('http://', 'https://', '//', 'mailto:', 'tel:', 'javascript:', 'data:')):
            continue
        if u.startswith('#'):
            if len(u) > 1 and u[1:] not in ids_by_file.get(f, set()):
                issues['锚点失效'].append((f, u))
            continue
        path, _, frag = u.partition('#')
        if not path:
            continue
        if path.endswith('.html'):
            if not os.path.exists(path):
                issues['死链'].append((f, u))
            elif frag and frag not in ids_by_file.get(path, set()):
                issues['死锚点(跨页)'].append((f, u))
        elif path.startswith('/'):
            if not os.path.exists(path.lstrip('/')):
                issues['死链(根路径)'].append((f, u))

# ---------------------------------------------------------------- 3) 结构问题
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    ids = re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', s)
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    if dup:
        issues['重复id'].append((f, ','.join(dup[:4])))
    imgs = re.findall(r'<img\b[^>]*>', s, re.I)
    noalt = [i for i in imgs if not re.search(r'\balt\s*=\s*["\'][^"\']+["\']', i, re.I)]
    if noalt:
        issues['img缺alt'].append((f, str(len(noalt))))
    if not re.search(r'<h1[\s>]', s, re.I):
        issues['缺h1'].append((f, ''))
    if not re.search(r'<meta[^>]+name\s*=\s*["\']description["\']', s, re.I):
        issues['缺description'].append((f, ''))
    if not re.search(r'<link[^>]+rel\s*=\s*["\']canonical["\']', s, re.I):
        issues['缺canonical'].append((f, ''))
    if not re.search(r'<meta[^>]+property\s*=\s*["\']og:url["\']', s, re.I):
        issues['缺og:url'].append((f, ''))
    # form 里没有 action / 没有 submit 按钮
    for fm in re.finditer(r'<form\b[^>]*>(.*?)</form>', s, re.S | re.I):
        tag = fm.group(0)[:400]
        if not re.search(r'action\s*=', tag, re.I):
            issues['form无action'].append((f, ''))
        if not re.search(r'type\s*=\s*["\']submit["\']|role\s*=\s*["\']button["\']', fm.group(1), re.I):
            issues['form无submit'].append((f, ''))

# ---------------------------------------------------------------- 4) 表单字段 ↔ 后端
FORM_FIELDS = {}
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    for fm in re.finditer(r'<form\b([^>]*)>(.*?)</form>', s, re.S | re.I):
        names = re.findall(r'name\s*=\s*["\']([^"\']+)["\']', fm.group(2))
        if names:
            FORM_FIELDS[f] = set(names)

# 后端字段白名单（从 api/_lib/fields.js 的 hidden 集合 + 已知字段推断）
api_booking = open('api/booking.js', encoding='utf-8').read()
api_contact = open('api/contact.js', encoding='utf-8').read()
known = set(re.findall(r"\b([a-zA-Z][a-zA-Z0-9_]*)\b", api_booking + api_contact))
STOP = {'const', 'let', 'var', 'function', 'return', 'if', 'else', 'try', 'catch', 'new', 'null',
        'true', 'false', 'undefined', 'module', 'exports', 'require', 'async', 'await', 'for',
        'of', 'in', 'this', 'typeof', 'instanceof', 'class', 'extends', 'constructor', 'super',
        'String', 'Number', 'Object', 'Array', 'JSON', 'Math', 'Date', 'RegExp', 'Error',
        'Promise', 'Set', 'Map', 'Boolean', 'parseInt', 'parseFloat', 'isFinite', 'encodeURIComponent',
        'decodeURIComponent', 'escapeHtml', 'first'}
known -= STOP

for f, names in FORM_FIELDS.items():
    miss = sorted(n for n in names if n not in known and not n.startswith('utm_') and n != 'extras')
    if miss:
        issues['表单字段后端未识别'].append((f, ','.join(miss[:8])))

# ---------------------------------------------------------------- 5) 外链（仅汇总）
ext = collections.Counter()
for f in htmls:
    s = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'(?:src|href)\s*=\s*["\'](https?://[^"\']+)["\']', s, re.I):
        ext[m.group(1).split('?')[0]] += 1

# ---------------------------------------------------------------- 6) 大文件
big = []
for root, dirs, files in os.walk('.'):
    if any(x in root for x in ('.git', 'node_modules', '.vercel')):
        continue
    for fn in files:
        p = os.path.join(root, fn)
        try:
            sz = os.path.getsize(p)
        except OSError:
            continue
        if sz > 600 * 1024:
            big.append((sz, p))
big.sort(reverse=True)

# ---------------------------------------------------------------- 输出
print('=' * 84)
print('站点静态体检（%d 个 HTML / %d 个 JS）' % (len(htmls), len(jsfiles)))
print('=' * 84)
total = 0
for k in sorted(issues, key=lambda x: -len(issues[x])):
    v = issues[k]
    total += len(v)
    print('\n【%s】%d 处' % (k, len(v)))
    for f, d in v[:8]:
        print('   %-28s %s' % (f.replace('.html', ''), str(d)[:110]))
    if len(v) > 8:
        print('   … 其余 %d 处' % (len(v) - 8))
print('\n合计问题：%d 处' % total)

print('\n' + '=' * 84)
print('体积最大的文件（>600KB）')
print('=' * 84)
for sz, p in big[:12]:
    print('   %7.1f MB  %s' % (sz / 1048576.0, p))
if not big:
    print('   无')

print('\n' + '=' * 84)
print('外链域名汇总')
print('=' * 84)
dom = collections.Counter()
for u, c in ext.items():
    d = re.sub(r'^\w+://', '', u).split('/')[0]
    dom[d] += c
for d, c in dom.most_common(14):
    print('   %4d  %s' % (c, d))

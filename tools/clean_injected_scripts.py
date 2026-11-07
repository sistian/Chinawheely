#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清除审计过程中注入到 HTML 的调试脚本残留（幂等）"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

MARKS = ['window.__errs', '__posts', 'o.formAction', 'o.hOverflow',
         'document.title=JSON.stringify', 'o.postsAfterEmpty', 'o.invalidCount']

SCRIPT = re.compile(r'<script\b[^>]*>.*?</script>', re.S | re.I)

removed = {}
for f in sorted(glob.glob('*.html')):
    s = open(f, encoding='utf-8').read()
    hits = []

    def repl(m):
        blk = m.group(0)
        if any(mk in blk for mk in MARKS):
            hits.append(blk)
            return ''
        return blk

    out = SCRIPT.sub(repl, s)
    # 清理注入后可能留下的空行堆积
    if hits:
        out = re.sub(r'\n{4,}', '\n\n\n', out)
        open(f, 'w', encoding='utf-8').write(out)
        removed[f] = len(hits)

print('清理 %d 个文件的注入残留：' % len(removed))
for f, n in removed.items():
    print('   %-24s %d 块' % (f.replace('.html', ''), n))

# 复查
print('\n--- 复查 ---')
left = []
for f in sorted(glob.glob('*.html')):
    s = open(f, encoding='utf-8', errors='ignore').read()
    for mk in MARKS:
        if mk in s:
            left.append((f, mk))
if left:
    print('   仍有残留: %s' % left[:10])
else:
    print('   注入残留 0 ✓')

bad = []
for f in sorted(glob.glob('*.html')):
    s = open(f, encoding='utf-8', errors='ignore').read()
    if '<body' not in s or '</body>' not in s or '<html' not in s or '</html>' not in s:
        bad.append(f)
print('   结构异常页: %d %s' % (len(bad), bad[:6]))

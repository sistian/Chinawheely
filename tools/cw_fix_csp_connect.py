#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给含 js/analytics.js 的页面补齐 CSP connect-src 的自建分析域名

背景：自建流量分析（api/analytics.js）需要前台跨域上报到
      https://api.chinawheely.com/api/analytics。
      站点页面的 <meta http-equiv="Content-Security-Policy"> 里
      connect-src 若没有该域名，浏览器会直接拦掉上报请求（静默失败、页面无感知）。

用法：
  python3 tools/cw_fix_csp_connect.py          # 只检查，报告缺哪些页（不改文件）
  python3 tools/cw_fix_csp_connect.py --apply  # 幂等修复：仅在 connect-src 中追加缺失域名

只做一件事：在 connect-src 指令里补 https://api.chinawheely.com（已存在则跳过）。
不改动其它任何 CSP 指令，也不改文件其它部分。
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEED = "https://api.chinawheely.com"


CSP_META_RE = [
    # 标准写法：<meta http-equiv="Content-Security-Policy" content="...">
    re.compile(r'(<meta\s+http-equiv="Content-Security-Policy"\s+content=")([^"]*)(")'),
    # 变体：<meta content="..." http-equiv="Content-Security-Policy"/>
    re.compile(r'(<meta\s+content=")([^"]*)("\s+http-equiv="Content-Security-Policy")'),
]


def csp_meta(s):
    for rx in CSP_META_RE:
        m = rx.search(s)
        if m:
            return m
    return None


def fix(s):
    m = csp_meta(s)
    if not m:
        return None
    csp = m.group(2)
    if NEED in csp:
        return None
    # 只在 connect-src 指令后追加域名，保持其余字符（含末尾分号）原样
    new_csp, n = re.subn(r'(connect-src)([^;]*)', lambda mm: mm.group(1) + mm.group(2) + ' ' + NEED, csp, count=1)
    if not n:
        return None
    return s[:m.start(2)] + new_csp + s[m.end(2):]


def main():
    apply = '--apply' in sys.argv
    changed, missing_csp = [], []
    for f in sorted(os.listdir(ROOT)):
        if not f.endswith('.html'):
            continue
        p = os.path.join(ROOT, f)
        try:
            s = open(p, encoding='utf-8').read()
        except Exception:
            continue
        if 'js/analytics.js' not in s:
            continue
        if not csp_meta(s):
            missing_csp.append(f)
            continue
        ns = fix(s)
        if ns is None:
            continue
        changed.append(f)
        if apply:
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(ns)

    print("需要补 connect-src 的页面：%d" % len(changed))
    if changed:
        print("  " + " ".join(changed[:20]) + (" ..." if len(changed) > 20 else ""))
    if missing_csp:
        print("没有 CSP meta 的页面：%d（%s）" % (len(missing_csp), " ".join(missing_csp[:10])))
    print("已应用修复" if apply else "仅检查，未写文件（加 --apply 应用）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

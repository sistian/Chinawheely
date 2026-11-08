#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理页面 <meta http-equiv="Content-Security-Policy"> 里的失效来源。

背景（2026-11-08 Vercel 迁移后）：
  1. 站点已从 GitHub Pages 迁到 Vercel，服务器层 CSP（vercel.json headers）已生效。
     浏览器会同时应用「服务器层 CSP」和「meta CSP」，并取两者的**交集**。
     因此 meta 里残留的失效来源必须清掉，否则会凭空缩小允许范围。
  2. formsubmit.co 是 2026-08 之前的第三方表单兜底方案，早已停用
     （全站 765+ 个 form 的 action 里已无一条指向它，只在 meta CSP 里还留着）。
  3. www.googletagmanager.com / google-analytics.com 是给 GA4 预留的，
     服务器层已补齐；meta 里保留或移除都可，但为口径一致统一保留。

做法（幂等）：
  - 仅改 connect-src / form-action / script-src 里的 formsubmit.co 条目
  - 改完每个文件只保留一条 meta CSP（原本就一条）
  - 不动其它任何内容

用法：
  python3 tools/cw_clean_meta_csp.py          # 预览
  python3 tools/cw_clean_meta_csp.py --apply  # 落盘
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

META_CSP_RE = re.compile(
    r'(<meta\s+http-equiv="Content-Security-Policy"\s+content=")([^"]*)(")'
)

# 需要从 connect-src / form-action / script-src 中移除的废弃来源
STALE = {
    'https://formsubmit.co',
}

# 允许出现在 script-src 里的（保留，因为服务器层也允许）
KEEP_SCRIPT = {
    'https://www.googletagmanager.com',
    'https://fonts.googleapis.com',
}


def clean_directive(directive):
    """清理单个 CSP 指令（如 "connect-src 'self' https://a https://b"）"""
    parts = directive.split()
    if len(parts) < 2:
        return directive
    name = parts[0]
    tokens = parts[1:]
    if name == 'script-src':
        # script-src 只保留仍需的
        keep = []
        for t in tokens:
            if t in STALE:
                continue
            keep.append(t)
        tokens = keep
    else:
        tokens = [t for t in tokens if t not in STALE]
    return ' '.join([name] + tokens)


def clean_csp(csp):
    directives = [d.strip() for d in csp.split(';') if d.strip()]
    out = []
    for d in directives:
        out.append(clean_directive(d))
    return '; '.join(out)


def main():
    apply = '--apply' in sys.argv
    files = sorted(f for f in os.listdir(ROOT)
                   if f.endswith('.html') and not f.startswith('.'))
    changed = 0
    for f in files:
        path = os.path.join(ROOT, f)
        with open(path, 'r', encoding='utf-8') as fh:
            src = fh.read()
        if 'formsubmit.co' not in src:
            continue

        def repl(m):
            return m.group(1) + clean_csp(m.group(2)) + m.group(3)

        new = META_CSP_RE.sub(repl, src)
        # 处理变体写法
        if new == src:
            var_re = re.compile(
                r'(<meta\s+content=")([^"]*)("\s+http-equiv="Content-Security-Policy")')
            new = var_re.sub(
                lambda m: m.group(1) + clean_csp(m.group(2)) + m.group(3), src)
        if new != src:
            changed += 1
            if apply:
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(new)
    print('扫描 %d 页，formsubmit.co 残留需清理 %d 页（%s）'
          % (len(files), changed, '已落盘' if apply else '仅预览'))

    # 复查
    left = 0
    for f in files:
        path = os.path.join(ROOT, f)
        with open(path, 'r', encoding='utf-8') as fh:
            if 'formsubmit.co' in fh.read():
                left += 1
    print('复查：仍含 formsubmit.co 的页面 %d' % left)
    return 0


if __name__ == '__main__':
    sys.exit(main())

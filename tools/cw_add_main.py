#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给缺少 <main> 地标的页面补上 <main>。

背景（2026-11-07）：全站 381 个根目录 HTML 缺 <main> 地标，其中 360 个是
城市页（可索引主力页）。<main> 是 HTML5 主内容地标，Google 用它判断
「这一段是正文」；缺它不影响排名，但补上是无风险的语义完善。

做法（保守、幂等、零视觉回归）：
  - 在 </nav> 之后、<footer> 之前找插入点，开 <main>
  - 在 <footer> 之前闭 </main>（nav / footer 留在 main 之外，语义正确）
  - 站点 CSS 里没有任何 main 选择器、也没有 body > 兄弟选择器，
    所以插入 main 元素不改变任何盒模型/布局 → 视觉零回归

⚠ 逐页校验（关键）：
  HTML5 解析规则里，<main> 起始标签会触发「关闭未闭合的 <p>」，
  </main> 结束标签会触发「隐式结束标签」。如果页面本身有未闭合的 <p>，
  插入 main 会让解析器在别处提前闭合 → 产生 end-tag-too-early 告警，
  极端情况下改变 DOM 结构。
  所以：每次插入都用 html5lib（= 浏览器/Google 的解析器）验证
    1) 错误数不增加
    2) DOM 结构除新增的 <main> 外完全一致
  不满足就换下一个候选插入点；全都不满足则跳过该页并报告。

用法：python3 tools/cw_add_main.py [--dry-run]
"""
import os
import re
import sys
import html5lib
import difflib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 跳过：本身就不是正文页的辅助工具页 / 内部文档 / 后台
SKIP = {
    '404.html', 'admin.html', 'image_downloader.html', 'batch_download.html',
    'manage-order.html', 'seo-swot-analysis.html',
}


def parse(s):
    """返回 (DOM 根节点, 解析错误列表)"""
    p = html5lib.HTMLParser(strict=False)
    p.parse(s)
    root = html5lib.parse(s, treebuilder='etree')
    return root, p.errors


def _tag(e):
    t = getattr(e, 'tag', None)
    if not isinstance(t, str):
        return None
    # etree builder 带命名空间 {http://www.w3.org/1999/xhtml}tag
    return t.rsplit('}', 1)[-1]


def skeleton(root):
    """DOM 骨架：标签 + class + id 的层级序列"""
    out = []

    def walk(e, d):
        tag = _tag(e)
        if tag is None:
            return  # Comment / PI
        out.append((d, tag, e.get('class', '') or '', e.get('id', '') or ''))
        for c in e:
            walk(c, d + 1)

    walk(root, 0)
    return out


def candidates(s):
    """给出候选插入点（必须在 nav 之后、footer 之前）

    排除移动端菜单（<div id="mobileMenu">）——它属于导航，不应包在 main 里。
    """
    nav = s.find('</nav>')
    foot = s.find('<footer')
    if nav < 0 or foot < 0:
        return []
    out = []
    for m in re.finditer(r'<(section|div)\b[^>]*>', s[nav:foot]):
        tag_text = m.group(0)
        if 'id="mobileMenu"' in tag_text or "id='mobileMenu'" in tag_text:
            continue
        out.append(nav + m.start())
    # 兜底：紧跟 </nav> 之后
    out.append(nav + len('</nav>'))
    seen, res = set(), []
    for p in out:
        if p not in seen:
            seen.add(p)
            res.append(p)
    return res


def try_fix(s, open_pos, close_pos):
    out = s[:open_pos] + '<main>\n' + s[open_pos:close_pos] + '</main>\n' + s[close_pos:]
    return out


def _unwrap_main(root):
    """把 <main> 节点拆开（用它的子节点取代它），返回新树。"""
    import copy
    t = copy.deepcopy(root)

    def walk(parent):
        i = 0
        while i < len(parent):
            child = parent[i]
            if _tag(child) == 'main':
                kids = list(child)
                parent.remove(child)
                for k in reversed(kids):
                    parent.insert(i, k)
                for k in kids:
                    walk(k)
                continue
            walk(child)
            i += 1

    walk(t)
    return t


def validate(orig, new):
    """返回 (ok, reason)"""
    t0, e0 = parse(orig)
    t1, e1 = parse(new)
    if len(e1) > len(e0):
        return False, f'解析错误增加 {len(e0)}→{len(e1)}'
    a = skeleton(t0)
    b = skeleton(_unwrap_main(t1))
    if a != b:
        return False, 'DOM 结构发生变化'
    return True, 'ok'


def fix(s):
    foot = s.find('<footer')
    for op in candidates(s):
        new = try_fix(s, op, foot)
        ok, why = validate(s, new)
        if ok:
            return new, True, why
    return s, False, 'no-valid-insertion-point'


def main():
    dry = '--dry-run' in sys.argv
    changed, failed = [], []
    for f in sorted(os.listdir(ROOT)):
        if not f.endswith('.html') or f in SKIP:
            continue
        p = os.path.join(ROOT, f)
        with open(p, encoding='utf-8', errors='ignore') as fh:
            s = fh.read()
        if '<main' in s:
            continue
        out, ch, why = fix(s)
        if ch:
            changed.append(f)
            if not dry:
                with open(p, 'w', encoding='utf-8') as fh:
                    fh.write(out)
        else:
            failed.append((f, why))
    print(f'补 <main> 地标：{len(changed)} 页' + ('（dry-run，未写盘）' if dry else ''))
    if failed:
        print(f'⚠️ 跳过 {len(failed)} 页（插入会改变解析结构，宁可不改）：')
        for f, why in failed[:20]:
            print(f'  {f}: {why}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

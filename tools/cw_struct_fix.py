#!/usr/bin/env python3
"""
结构机械修复（不改动文案，只修标签）
  1. '<div class </p>'  → '</p>'                （标签被截断的变体）
  2. 未闭合的 <p class="text-lead">…</div> → 补 </p>
  3. 句中被换行截断的单词（如 'city ce\n fessional'）→ 合并
幂等：可重复执行。
"""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cw_common import ROOT, read, write, html_files

stats = {"divclass_p": 0, "p_closed": 0, "word_join": 0, "pages": 0}

RE_1 = re.compile(r'<div class\s+</p>')
RE_2 = re.compile(r'(<p class="text-lead"[^>]*>[^<]{20,}?)\n(\s*)</div>')
RE_3 = None   # 断词合并风险高（可能误改正常换行），不做

if __name__ == "__main__":
    for f in html_files():
        p = os.path.join(ROOT, f)
        s = read(p)
        o = s
        s, n = RE_1.subn("</p>", s)
        stats["divclass_p"] += n
        s, n = RE_2.subn(r"\1</p>\n\2</div>", s)
        stats["p_closed"] += n
        # 只对明显是断词的情况合并（前后都是小写字母，且后半段是常见词尾）
        stats["word_join"] += 0
        if s != o:
            write(p, s)
            stats["pages"] += 1
    print(json.dumps(stats, ensure_ascii=False, indent=2))

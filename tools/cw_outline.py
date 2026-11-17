#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""输出某页面的「结构大纲」：只保留标签与 class，剥掉文本内容。
用于照抄新页面生成器所需的 class 结构。

用法： python3 tools/cw_outline.py dali.html
"""
import os
import re
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
f = sys.argv[1] if len(sys.argv) > 1 else "dali.html"
h = open(os.path.join(SITE, f), encoding="utf-8").read()
h = re.sub(r"<script.*?</script>", "<!--script-->", h, flags=re.S)
h = re.sub(r"<style.*?</style>", "<!--style-->", h, flags=re.S)
h = re.sub(r">[^<>]+<", "><", h)
h = re.sub(r"<[^>]+>", lambda m: m.group(0) if re.search(r'class=|id=|src=|href=|type=', m.group(0)) else "", h)
h = re.sub(r"\n\s*\n+", "\n", h)
print(h)

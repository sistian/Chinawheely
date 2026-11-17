#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打印若干可疑页面的正文关键段落，用于人工判定城市真实身份。"""
import os
import re
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def body(slug):
    f = os.path.join(SITE, slug + ".html")
    if not os.path.exists(f):
        return ""
    h = open(f, encoding="utf-8", errors="replace").read()
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S)
    h = re.sub(r"<!--.*?-->", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()


for slug in sys.argv[1:]:
    t = body(slug)
    print(f"\n{'='*70}\n### {slug}  (len {len(t)})\n")
    print(t[:1800])

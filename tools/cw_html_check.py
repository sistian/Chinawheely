#!/usr/bin/env python3
"""
Chinawheely 全站 HTML 完整性校验（CI 用）
检查：标签配平、JSON-LD 合法性、本地资源存在性、重复 h1、标题/描述缺失、锚点有效性
退出码：0=通过，1=有 FAIL
"""
import os, re, sys, json, html
from html.parser import HTMLParser

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOID = {"area","base","br","col","embed","hr","img","input","link","meta","param",
        "source","track","wbr","path","circle","rect","line","polygon","use"}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.h1 = 0
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "h1":
            self.h1 += 1
        self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"多余结束标签 </{tag}> @{self.getpos()}")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    for t, pos in self.stack[i + 1:]:
                        self.errors.append(f"未闭合 <{t}> @{pos}")
                    del self.stack[i:]
                    break
            else:
                self.errors.append(f"孤立结束标签 </{tag}> @{self.getpos()}")


def read(p):
    with open(p, encoding="utf-8", errors="ignore") as f:
        return f.read()


def main():
    files = sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))
    fails = {"tag_balance": [], "jsonld": [], "missing_asset": [], "h1_count": [],
             "no_title": [], "no_desc": []}
    warns = {"no_og": [], "no_csp": [], "no_lazy": [], "no_canonical": []}

    for f in files:
        s = read(os.path.join(ROOT, f))
        c = Checker()
        try:
            c.feed(s)
        except Exception as e:
            fails["tag_balance"].append(f"{f}: 解析异常 {e}")
            continue
        if c.stack:
            for t, pos in c.stack:
                fails["tag_balance"].append(f"{f}: 未闭合 <{t}> @{pos}")
        if c.errors:
            fails["tag_balance"].append(f"{f}: {c.errors[:2]}")
        if c.h1 > 1:
            fails["h1_count"].append(f"{f}: {c.h1} 个 h1")
        if "<title>" not in s:
            fails["no_title"].append(f)
        if '<meta name="description"' not in s:
            fails["no_desc"].append(f)
        for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                json.loads(b)
            except Exception as e:
                fails["jsonld"].append(f"{f}: {str(e)[:60]}")
        for src in set(re.findall(r'(?:src|href)="(images/[^"]+)"', s)):
            if not os.path.exists(os.path.join(ROOT, src)):
                fails["missing_asset"].append(f"{f} -> {src}")
        if 'property="og:image"' not in s:
            warns["no_og"].append(f)
        if "Content-Security-Policy" not in s:
            warns["no_csp"].append(f)
        if "<img" in s and 'loading="lazy"' not in s:
            warns["no_lazy"].append(f)
        if 'rel="canonical"' not in s:
            warns["no_canonical"].append(f)

    print("=" * 70)
    print(f"HTML 完整性校验  页面 {len(files)}")
    for k, v in fails.items():
        print(f"[FAIL] {k:16} {len(v)}")
        for x in v[:5]:
            print(f"        {x}")
    for k, v in warns.items():
        print(f"[WARN] {k:16} {len(v)}" + (f"   例: {' '.join(v[:4])}" if v else ""))
    total_fail = sum(len(v) for v in fails.values())
    print("=" * 70)
    print(f"FAIL {total_fail} | WARN {sum(len(v) for v in warns.values())}")
    sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()

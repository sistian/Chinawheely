#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标题层级规范化（策略一 P0）
  1. 消除跳级：相邻标题层级差 > 1 时，把后一个降到 prev+1
  2. 改标签时加 .lvl-hN（原级别）类，保留原视觉
  3. 若改后会被某条 scoped 规则（如 .hero-card h3）命中，则写 inline font-size 保原样
  4. 页脚分组标题移出文档大纲（h1-h4 → div.footer-h）
  5. H1 唯一化：多余 H1 降为 H2
用法: python3 tools/fix_heading_hierarchy.py [--dry]
"""
import re
import os
import sys

HRE = re.compile(r"(?is)<h([1-6])\b([^>]*)>")
PROTECT = re.compile(r"(?is)<(script|style|noscript|template)\b[^>]*>.*?</\1\s*>|<!--.*?-->")
TAG = re.compile(r"(?s)<[^>]+>")
ATTR_CL = re.compile(r'(?i)\bclass\s*=\s*"([^"]*)"')
ATTR_ID = re.compile(r'(?i)\bid\s*=\s*"([^"]*)"')
ATTR_STYLE = re.compile(r'(?i)\bstyle\s*=\s*"([^"]*)"')
COMPOUND = re.compile(r"^([a-zA-Z][a-zA-Z0-9]*)?((?:\.[\w-]+)*)((?:::?[\w-]+(?:\([^)]*\))?)*)$")
VOID = set("area base br col embed hr img input link meta source track wbr".split())
BASE_SIZE = {"h1": "2em", "h2": "1.5em", "h3": "1.17em", "h4": "1em", "h5": "0.83em", "h6": "0.67em"}


def esc_attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;")


def mask(text):
    def rep(m):
        return "".join(ch if ch == "\n" else " " for ch in m.group(0))
    return PROTECT.sub(rep, text)


def add_class(attrs, cls):
    m = ATTR_CL.search(attrs)
    if m:
        if cls in m.group(1).split():
            return attrs
        return attrs[:m.start(1)] + m.group(1) + " " + cls + attrs[m.end(1):]
    return attrs.rstrip() + ' class="%s"' % cls


def add_style(attrs, prop):
    m = ATTR_STYLE.search(attrs)
    if m:
        if prop.split(":")[0] in m.group(1):
            return attrs
        return attrs[:m.end(1)] + ";" + prop + attrs[m.end(1):]
    return attrs.rstrip() + ' style="%s"' % prop


def walk_css(css):
    """产出 (selector, declarations dict) 按文档顺序"""
    out = []
    i, n = 0, len(css)
    stack, buf, buf_start = [], "", 0
    while i < n:
        ch = css[i]
        if ch == "{":
            stack.append([buf.strip(), i + 1, buf_start])
            buf, buf_start = "", i + 1
        elif ch == "}":
            if stack:
                pr, bs, ps = stack.pop()
                if not pr.startswith("@"):
                    decls = {}
                    for d in css[bs:i].split(";"):
                        if ":" in d:
                            k, v = d.split(":", 1)
                            decls[k.strip().lower()] = v.strip()
                    out.append((pr, decls, ps, i + 1))
            buf, buf_start = "", i + 1
        else:
            if not buf:
                buf_start = i
            buf += ch
        i += 1
    return out


def collect_scoped(css_text):
    """收集带 scoped 前缀的字号规则: {tag: [(classes_set, value, important)]}"""
    scoped = {}
    for pr, decls, ps, pe in walk_css(css_text):
        fs = decls.get("font-size")
        if not fs:
            continue
        imp = "!important" in fs
        val = fs.replace("!important", "").strip()
        for sel in pr.split(","):
            sel = sel.strip()
            parts = sel.split()
            if len(parts) < 2:
                continue
            m = COMPOUND.match(parts[-1])
            if not m:
                continue
            tag, classes, pseudo = m.groups()
            if not tag or not re.fullmatch(r"h[1-6]", tag):
                continue
            pre = set()
            for pt in parts[:-1]:
                pre.update(re.findall(r"\.([\w-]+)", pt))
            if not pre:
                continue
            scoped.setdefault(tag, []).append((pre, val, imp))
    return scoped


def scan_headings(masked):
    """基于正则定位标题（对损坏 HTML 免疫）；祖先 class 用窗口扫描近似"""
    res = []
    for m in re.finditer(r"(?is)<h([1-6])\b([^>]*)>(.*?)</h\1\s*>", masked):
        attrs = m.group(2) or ""
        inner = m.group(3)
        cm = ATTR_CL.search(attrs)
        own = set(cm.group(1).split()) if cm else set()
        # 祖先 class：取标题前 1500 字符内的 class 属性（末尾若干个）
        win = masked[max(0, m.start() - 1500):m.start()]
        anc = set()
        for am in ATTR_CL.finditer(win):
            anc.update(am.group(1).split())
        res.append({"start": m.start(), "end": m.end(), "level": int(m.group(1)), "attrs": attrs,
                    "inner": inner, "anc": anc, "own": own})
    return res


def eff_size(scoped, tag, anc_classes):
    """元素在给定标签下的有效字号（scoped 规则优先，最后命中者胜）"""
    best = None
    for t, rules in scoped.items():
        if t != tag:
            continue
        for pre, val, imp in rules:
            if pre and pre <= anc_classes:
                best = (val, imp, pre)
    if best:
        return best[0], best[1]
    return BASE_SIZE.get(tag, "1em"), False


def fix_page(html, scoped, dry=False):
    st = {"changed": 0, "footer": 0, "h1_fixed": 0, "inline": 0}
    masked = mask(html)
    fspans = [(m.start(), m.end()) for m in re.finditer(r"(?is)<footer\b[^>]*>.*?</footer\s*>", masked)]

    def in_footer(pos):
        return any(a <= pos < b for a, b in fspans)

    hs = scan_headings(masked)
    body = [h for h in hs if not in_footer(h["start"])]
    # 计算新级别
    prev = 0
    for h in body:
        lv = h["level"]
        nl = lv if not prev else (prev + 1 if lv > prev + 1 else lv)
        nl = max(1, min(6, nl))
        h["new"] = nl
        prev = nl
    # H1 唯一
    seen = False
    for h in body:
        if h["new"] == 1:
            if seen:
                h["new"] = 2
                st["h1_fixed"] += 1
            else:
                seen = True

    repl = []
    for h in hs:
        if in_footer(h["start"]):
            if h["level"] >= 5:
                continue
            na = add_class(h["attrs"], "footer-h")
            repl.append((h["start"], h["end"], "<div%s>%s</div>" % (na, h["inner"])))
            st["footer"] += 1
            continue
        nl = h["new"]
        if nl == h["level"]:
            continue
        anc_classes = h["anc"]
        # 新标签会不会命中 scoped 规则（原来没命中）→ 需要 inline 保原样
        new_val, new_imp = eff_size(scoped, "h%d" % nl, anc_classes)
        old_val, old_imp = eff_size(scoped, "h%d" % h["level"], anc_classes)
        scoped_new_hit = False
        for t, rules in scoped.items():
            if t != "h%d" % nl:
                continue
            for pre, val, imp in rules:
                if pre and pre <= anc_classes:
                    scoped_new_hit = True
        na = add_class(h["attrs"], "lvl-h%d" % h["level"])
        if scoped_new_hit and new_val != old_val:
            na = add_style(na, "font-size:%s%s" % (old_val, " !important" if old_imp else ""))
            st["inline"] += 1
        repl.append((h["start"], h["end"], "<h%d%s>%s</h%d>" % (nl, na, h["inner"], nl)))
        st["changed"] += 1

    if not repl:
        return html, st
    out, pos = [], 0
    for a, b, r in repl:
        out.append(html[pos:a])
        out.append(r)
        pos = b
    out.append(html[pos:])
    return "".join(out), st


def load_css(root):
    css = ""
    for dp, dn, fn in os.walk(root):
        if ".git" in dp or "node_modules" in dp:
            continue
        for f in fn:
            if f.endswith(".css"):
                css += open(os.path.join(dp, f), encoding="utf-8", errors="replace").read() + "\n"
    return css


def main():
    dry = "--dry" in sys.argv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scoped = collect_scoped(load_css(root))
    print("scoped 字号规则:", {k: len(v) for k, v in scoped.items()})
    tot = {"changed": 0, "footer": 0, "h1_fixed": 0, "inline": 0}
    files = 0
    for dp, dn, fn in os.walk(root):
        if ".git" in dp or "node_modules" in dp:
            continue
        rel = os.path.relpath(dp, root)
        if rel.split(os.sep)[0] in ("tools", "node_modules"):
            continue
        for f in sorted(fn):
            if not f.endswith(".html"):
                continue
            p = os.path.join(dp, f)
            s = open(p, encoding="utf-8", errors="replace").read()
            new, st = fix_page(s, scoped)
            if new != s:
                files += 1
                for k in tot:
                    tot[k] += st[k]
                if not dry:
                    open(p, "w", encoding="utf-8").write(new)
    print(("DRY " if dry else "") + "改动 %d 文件 | 改级 %d | 页脚 %d | 多余H1 %d | inline保视觉 %d"
          % (files, tot["changed"], tot["footer"], tot["h1_fixed"], tot["inline"]))


if __name__ == "__main__":
    main()

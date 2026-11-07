#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
站点暗病修复（幂等）
1) index.html 三处 href="#"（logo / Home 导航 / Footer Home）→ index.html
2) juancheng.html 的 "View Details & Book" 按钮 href="#" → booking 页
3) 10 个城市页的 "Tea Culture" 卡片指向本页不存在的 #tea 锚点 → 改指向对应的
   *-tea-culture.html 主题页
4) 19 个城市页重复 id="best-time"（两个 section 同 id，HTML 无效）→ 第二处改 best-time-guide
5) 6 个真实页缺 <main> 地标 → 补（301 跳转桩页不需要）
"""
import glob, os, re, collections, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

TEA_TARGETS = {
    'chongqing.html': 'chongqing-tea-culture.html',
    'dalian.html': 'dalian-tea-culture.html',
    'harbin.html': 'harbin-tea-culture.html',
    'jinan.html': 'jinan-tea-culture.html',
    'qingdao.html': 'qingdao-tea-culture.html',
    'shanghai.html': 'shanghai-tea-culture.html',
    'shenzhen.html': 'shenzhen-tea-culture.html',
    'tianjin.html': 'tianjin-tea-culture.html',
    'wuhan.html': 'wuhan-tea-culture.html',
    'xian.html': 'xian-tea-culture.html',
}

MAIN_PAGES = ['404.html', 'admin.html', 'batch_download.html', 'image_downloader.html',
              'manage-order.html', 'seo-swot-analysis.html']


def jsonld_ok(s):
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(b.strip())
        except Exception as e:
            return str(e)[:80]
    return None


def fix_main(html):
    """给页面补 <main> 地标：把 body 内的内容包进 <main>
    注意：第一个捕获组是 <body> 标签本身，不是文档头（此前误用导致 <head> 被吞）"""
    if re.search(r'<main[\s>]', html, re.I):
        return html, False
    m = re.search(r'(<body[^>]*>)(.*)(</body>)', html, re.S | re.I)
    if not m:
        return html, False
    # 必须按字符偏移切，不能用 groups()（groups 只给捕获组，会丢掉 <body> 之前的 head）
    pre = html[:m.end(1)]                   # 含 <!DOCTYPE html>...<body ...>（到 <body> 标签结束）
    body = m.group(2)                      # body 内部内容
    post = html[m.end(3):]                 # </body> 之后（不含 </body> 本身）
    cm = re.search(r'(<div class="container[^"]*">)(.*?)(</div>\s*(?:</body>|</main>))', body, re.S)
    if cm:
        newbody = body[:cm.start()] + '<main>' + cm.group(0) + '</main>' + body[cm.end():]
        return pre + newbody + '</body>' + post, True
    return pre + '<main>' + body + '</main>' + '</body>' + post, True


def main():
    changed = {}
    files = sorted(glob.glob('*.html'))
    for f in files:
        s = open(f, encoding='utf-8').read()
        o = s
        n = 0

        # ① index.html 空 href
        if f == 'index.html':
            c = s.count('href="#"')
            if c:
                s = s.replace('href="#"', 'href="index.html"')
                n += c

        # ② juancheng 死按钮
        if f == 'juancheng.html':
            old = '<a href="#" class="btn btn-outline" style="margin-top:var(--space-3);">View Details & Book →</a>'
            new = ('<a href="booking.html?city=Juancheng%20(Shandong)" class="btn btn-outline" '
                   'style="margin-top:var(--space-3);">View Details & Book →</a>')
            if old in s:
                s = s.replace(old, new)
                n += 1

        # ③ #tea 死锚点
        if f in TEA_TARGETS:
            old = 'href="%s#tea"' % f
            new = 'href="%s"' % TEA_TARGETS[f]
            if old in s:
                c = s.count(old)
                s = s.replace(old, new)
                n += c

        # ④ 重复 id="best-time"：第二个改成 best-time-guide
        if s.count('id="best-time"') > 1:
            idx = s.find('id="best-time"')
            idx2 = s.find('id="best-time"', idx + 5)
            s = s[:idx2] + 'id="best-time-guide"' + s[idx2 + len('id="best-time"'):]
            n += 1

        # ⑤ 补 main
        if f in MAIN_PAGES:
            s, did = fix_main(s)
            if did:
                n += 1

        if s != o:
            err = jsonld_ok(s)
            if err:
                print('!! %s JSON-LD 非法：%s —— 已跳过' % (f, err))
                continue
            open(f, 'w', encoding='utf-8').write(s)
            changed[f] = n

    print('修改 %d 个文件：' % len(changed))
    for f, n in sorted(changed.items()):
        print('   %-26s %d 处' % (f.replace('.html', ''), n))

    # ---------------- 复查 ----------------
    print('\n--- 复查 ---')
    files = sorted(glob.glob('*.html'))
    ids_by = {}
    for f in files:
        s = open(f, encoding='utf-8', errors='ignore').read()
        ids_by[f] = set(re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', s))

    empty = []
    dead_tea = []
    dup_id = []
    no_main = []
    for f in files:
        s = open(f, encoding='utf-8', errors='ignore').read()
        if re.search(r'<a\b[^>]*href\s*=\s*["\'](?:#|["\'])["\']', s, re.I):
            empty.append(f)
        for m in re.finditer(r'href\s*=\s*["\']([^"\']+\.html#tea)["\']', s, re.I):
            p, _, fr = m.group(1).partition('#')
            if os.path.exists(p) and fr not in ids_by.get(p, set()):
                dead_tea.append((f, m.group(1)))
        ids = re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', s)
        d = [k for k, v in collections.Counter(ids).items() if v > 1]
        if d:
            dup_id.append((f, d))
        if not re.search(r'<main[\s>]', s, re.I) and 'http-equiv="refresh"' not in s:
            no_main.append(f)

    print('   空 href 页面: %d %s' % (len(empty), ', '.join(x.replace('.html', '') for x in empty[:8])))
    print('   #tea 死锚点: %d %s' % (len(dead_tea), dead_tea[:5]))
    print('   重复 id 页面: %d %s' % (len(dup_id), dup_id[:5]))
    print('   缺 main 页面: %d %s' % (len(no_main), ', '.join(x.replace('.html', '') for x in no_main[:10])))


if __name__ == '__main__':
    main()

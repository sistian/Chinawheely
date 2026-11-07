#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行时体检：批量无头 Chrome 打开页面，抓 console 错误 / JS 异常 / 图片加载失败 /
关键 DOM 缺失 / 重复 id / 移动端横向溢出
"""
import json, os, re, subprocess, sys, threading, functools, http.server, socketserver, random

ROOT = "/Users/w/Desktop/Chinawheely 10.27"
PORT = 8791
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

INJECT = """
<script>
window.__errs=[];
window.addEventListener('error',function(e){window.__errs.push('JS: '+(e.message||'')+' @ '+(e.filename||'').split('/').pop()+':'+(e.lineno||''));});
window.addEventListener('unhandledrejection',function(e){window.__errs.push('Promise: '+String(e.reason).slice(0,120));});
var _ce=console.error; console.error=function(){ window.__errs.push('console.error: '+Array.prototype.join.call(arguments,' ').slice(0,160)); _ce.apply(console,arguments); };
var _cw=console.warn; console.warn=function(){ window.__errs.push('console.warn: '+Array.prototype.join.call(arguments,' ').slice(0,160)); _cw.apply(console,arguments); };
setTimeout(function(){
 var o={};
 o.errs=window.__errs.slice(0,6);
 o.imgs=document.querySelectorAll('img').length;
 o.imgBroken=0; var broken=[];
 Array.prototype.forEach.call(document.querySelectorAll('img'),function(im){ if(im.complete && im.naturalWidth===0){o.imgBroken++; if(broken.length<3)broken.push(im.getAttribute('src'));} });
 o.brokenList=broken;
 o.h1=(document.querySelectorAll('h1').length);
 o.main=document.querySelectorAll('main').length;
 o.footer=document.querySelectorAll('footer').length;
 o.hOverflow=document.documentElement.scrollWidth > window.innerWidth+2;
 o.dupIds=[];
 var ids={},dups=[];
 Array.prototype.forEach.call(document.querySelectorAll('[id]'),function(e){var i=e.id; if(ids[i]){if(dups.indexOf(i)<0)dups.push(i);} else ids[i]=1;});
 o.dupIds=dups.slice(0,4);
 o.forms=document.querySelectorAll('form').length;
 o.inputs=document.querySelectorAll('input,select,textarea').length;
 o.links=document.querySelectorAll('a').length;
 o.emptyHref=0;
 Array.prototype.forEach.call(document.querySelectorAll('a'),function(a){var h=a.getAttribute('href'); if(h===''||h==='#')o.emptyHref++;});
 o.title=(document.title||'').slice(0,60);
 document.title=JSON.stringify(o);
},2600);
</script>
"""


def pick_pages():
    pages = []
    core = ['index.html', 'booking.html', 'contact.html', 'help.html', 'faq.html', 'services.html',
            'about.html', 'prices.html', 'terms.html', 'cancellation.html', 'manage-order.html',
            'thank-you.html', '404.html', 'cities.html', 'city-charter.html', 'airport-transfer.html',
            'blog.html', 'careers.html', 'partners.html', 'cookies.html', 'seo-swot-analysis.html']
    for c in core:
        if os.path.exists(os.path.join(ROOT, c)):
            pages.append(c)
    cities = sorted([f for f in os.listdir(ROOT) if f.endswith('.html') and f[:-5] not in core])
    random.seed(7)
    sample = random.sample(cities, min(45, len(cities)))
    pages += sorted(sample)
    # 主题页
    for pref in ['tea-culture', 'best-time', 'day-trips', 'photo-spots', 'food-shopping']:
        th = [c for c in cities if c.startswith(pref)]
        pages += th[:2]
    return pages


def run(url, w=1280, h=900):
    args = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=9000",
            f"--window-size={w},{h}", "--dump-dom", url]
    p = subprocess.run(args, capture_output=True, text=True, timeout=120)
    m = re.search(r'<title>(.*?)</title>', p.stdout, re.S)
    if not m:
        return {'fatal': 'no title'}
    t = m.group(1).strip()
    try:
        return json.loads(t)
    except Exception:
        return {'raw_title': t[:120]}


def main():
    pages = pick_pages()
    print('扫描 %d 个页面（每个页面注入错误捕获）…' % len(pages))

    # 临时注入到所有页面
    originals = {}
    for pg in pages:
        fp = os.path.join(ROOT, pg)
        o = open(fp, encoding='utf-8').read()
        originals[pg] = o
        if '</body>' in o:
            open(fp, 'w', encoding='utf-8').write(o.replace('</body>', INJECT + '</body>'))

    Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    bad = []
    try:
        for i, pg in enumerate(pages, 1):
            r = run("http://127.0.0.1:%d/%s" % (PORT, pg))
            issues = []
            if r.get('fatal') or 'raw_title' in r:
                issues.append('渲染异常 ' + str(r)[:80])
            else:
                if r.get('errs'):
                    issues.append('JS错误 ' + ' || '.join(r['errs'])[:220])
                if r.get('imgBroken'):
                    issues.append('图片加载失败 %d 个: %s' % (r['imgBroken'], r.get('brokenList')))
                if r.get('dupIds'):
                    issues.append('重复id ' + ','.join(r['dupIds']))
                if r.get('hOverflow'):
                    issues.append('横向溢出')
                if r.get('emptyHref'):
                    issues.append('空href链接 %d 个' % r['emptyHref'])
                if r.get('h1') == 0:
                    issues.append('无h1')
                if r.get('main') == 0:
                    issues.append('无main')
                if r.get('forms') and r.get('inputs') == 0:
                    issues.append('有form无输入')
            if issues:
                bad.append((pg, issues))
                print('  ⚠ %-26s %s' % (pg.replace('.html', ''), ' | '.join(issues)[:240]))
            if i % 10 == 0:
                print('  …已扫 %d/%d' % (i, len(pages)))
    finally:
        for pg, o in originals.items():
            open(os.path.join(ROOT, pg), 'w', encoding='utf-8').write(o)
        httpd.shutdown()

    print('\n' + '=' * 80)
    print('扫描完成：%d/%d 个页面有问题' % (len(bad), len(pages)))
    for pg, iss in bad:
        print('  %-26s %s' % (pg.replace('.html', ''), ' | '.join(iss)[:260]))


if __name__ == '__main__':
    main()

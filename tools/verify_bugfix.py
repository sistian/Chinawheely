#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复后回归：结构 + 运行时（重点是加了 <main> 的 6 个页）"""
import functools, http.server, json, os, re, socketserver, subprocess, threading

ROOT = "/Users/w/Desktop/Chinawheely 10.27"
PORT = 8803
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

INJECT = """
<script>
window.__errs=[];
window.addEventListener('error',function(e){window.__errs.push('JS: '+(e.message||''));});
setTimeout(function(){
 var o={};
 o.errs=window.__errs.slice(0,4);
 o.main=document.querySelectorAll('main').length;
 o.bodyMain=(document.body.innerHTML.match(/<main/g)||[]).length;
 o.footer=document.querySelectorAll('footer').length;
 o.h1=document.querySelectorAll('h1').length;
 o.imgs=document.querySelectorAll('img').length;
 o.imgBroken=0; Array.prototype.forEach.call(document.querySelectorAll('img'),function(im){if(im.complete&&im.naturalWidth===0)o.imgBroken++;});
 o.hOverflow=document.documentElement.scrollWidth>window.innerWidth+2;
 o.text=(document.body.innerText||'').replace(/\\s+/g,' ').trim().length;
 document.title=JSON.stringify(o);
},2200);
</script>
"""

PAGES = ['404.html', 'admin.html', 'manage-order.html', 'batch_download.html',
         'image_downloader.html', 'seo-swot-analysis.html', 'index.html', 'juancheng.html',
         'chongqing.html', 'xian.html', 'booking.html', 'contact.html', 'help.html',
         'prices.html', 'terms.html', 'services.html', 'thank-you.html', 'faq.html']


def run(url):
    args = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=8000",
            "--window-size=1280,900", "--dump-dom", url]
    p = subprocess.run(args, capture_output=True, text=True, timeout=120)
    m = re.search(r'<title>(.*?)</title>', p.stdout, re.S)
    if not m:
        return {'fatal': 'no title'}
    try:
        return json.loads(m.group(1).strip())
    except Exception:
        return {'raw': m.group(1)[:100]}


def main():
    originals = {}
    for pg in PAGES:
        fp = os.path.join(ROOT, pg)
        if not os.path.exists(fp):
            continue
        o = open(fp, encoding='utf-8').read()
        originals[pg] = o
        if '</body>' in o:
            open(fp, 'w', encoding='utf-8').write(o.replace('</body>', INJECT + '</body>'))

    Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        for pg in PAGES:
            if pg not in originals:
                continue
            r = run("http://127.0.0.1:%d/%s" % (PORT, pg))
            flag = 'OK ' if not r.get('errs') and r.get('imgBroken', 0) == 0 and not r.get('hOverflow') else '⚠  '
            print('  %s%-26s main=%s footer=%s h1=%s img=%s/broken=%s overflow=%s text=%s %s' % (
                flag, pg.replace('.html', ''), r.get('main'), r.get('footer'), r.get('h1'),
                r.get('imgs'), r.get('imgBroken'), r.get('hOverflow'), r.get('text'),
                (r.get('errs') or [''])[0][:80]))
    finally:
        for pg, o in originals.items():
            open(os.path.join(ROOT, pg), 'w', encoding='utf-8').write(o)
        httpd.shutdown()


if __name__ == '__main__':
    main()

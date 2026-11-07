#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contact.html 定向运行时检查"""
import functools, http.server, json, os, re, socketserver, subprocess, threading

ROOT = "/Users/w/Desktop/Chinawheely 10.27"
PORT = 8873
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

INJECT = """
<script>
window.__errs=[];
window.addEventListener('error',function(e){window.__errs.push(String(e.message));});
setTimeout(function(){
 var o={};
 o.errs=window.__errs.slice(0,5);
 o.main=document.querySelectorAll('main').length;
 o.footer=document.querySelectorAll('footer').length;
 o.h1=document.querySelectorAll('h1').length;
 o.imgs=document.querySelectorAll('img').length;
 o.imgBroken=0; Array.prototype.forEach.call(document.querySelectorAll('img'),function(im){if(im.complete&&im.naturalWidth===0)o.imgBroken++;});
 o.hOverflow=document.documentElement.scrollWidth>window.innerWidth+2;
 o.text=(document.body.innerText||'').replace(/\\s+/g,' ').trim().length;
 o.hasForm=!!document.getElementById('contactForm');
 o.secOk=!!(window.ChinawheelySecurity);
 o.rateLimiter=!!(window.ChinawheelySecurity && window.ChinawheelySecurity.rateLimiter);
 o.emailValid=(window.ChinawheelySecurity && window.ChinawheelySecurity.isValidEmail)? window.ChinawheelySecurity.isValidEmail('a@b.co') : 'noFn';
 document.title=JSON.stringify(o);
},2500);
</script>
"""


def run(url):
    args = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=9000",
            "--window-size=1280,900", "--dump-dom", url]
    p = subprocess.run(args, capture_output=True, text=True, timeout=120)
    m = re.search(r'<title>(.*?)</title>', p.stdout, re.S)
    if not m:
        return {'fatal': 'no title', 'stderr': p.stderr[-200:]}
    try:
        return json.loads(m.group(1).strip())
    except Exception:
        return {'raw': m.group(1)[:200]}


def main():
    fp = os.path.join(ROOT, 'contact.html')
    o = open(fp, encoding='utf-8').read()
    open(fp, 'w', encoding='utf-8').write(o.replace('</body>', INJECT + '</body>'))
    Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        r = run("http://127.0.0.1:%d/contact.html" % PORT)
        print(json.dumps(r, ensure_ascii=False, indent=1))
    finally:
        open(fp, 'w', encoding='utf-8').write(o)
        httpd.shutdown()


if __name__ == '__main__':
    main()

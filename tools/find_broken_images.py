#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""找出加载失败的图片（本地 + 线上）"""
import functools, http.server, json, os, re, socketserver, subprocess, threading

ROOT = "/Users/w/Desktop/Chinawheely 10.27"
PORT = 8817
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

INJECT = """
<script>
setTimeout(function(){
 var bad=[];
 Array.prototype.forEach.call(document.querySelectorAll('img'),function(im){
   if(im.complete && im.naturalWidth===0){
     bad.push({src:im.getAttribute('src'), cls:im.className, alt:im.getAttribute('alt'), parent:(im.parentElement||{}).className});
   }
 });
 var bg=[];
 Array.prototype.forEach.call(document.querySelectorAll('[style*="url("]'),function(e){
   var st=e.getAttribute('style')||''; var m=st.match(/url\\(["']?([^"')]+)["']?\\)/);
   if(m) bg.push({tag:e.tagName, url:m[1], cls:e.className});
 });
 document.title=JSON.stringify({broken:bad, bgCount:bg.length});
},3000);
</script>
"""


def run(url):
    args = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=9000",
            "--window-size=1280,900", "--dump-dom", url]
    p = subprocess.run(args, capture_output=True, text=True, timeout=120)
    m = re.search(r'<title>(.*?)</title>', p.stdout, re.S)
    if not m:
        return {'fatal': 'no title'}
    try:
        return json.loads(m.group(1).strip())
    except Exception:
        return {'raw': m.group(1)[:200]}


def main():
    fp = os.path.join(ROOT, 'index.html')
    o = open(fp, encoding='utf-8').read()
    open(fp, 'w', encoding='utf-8').write(o.replace('</body>', INJECT + '</body>'))
    Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        r = run("http://127.0.0.1:%d/index.html" % PORT)
        print('本地 index.html:')
        print(json.dumps(r, ensure_ascii=False, indent=1)[:1500])
    finally:
        open(fp, 'w', encoding='utf-8').write(o)
        httpd.shutdown()

    # 线上同样检测
    r2 = run("https://www.chinawheely.com/index.html")
    print('\n线上 index.html:')
    print(json.dumps(r2, ensure_ascii=False, indent=1)[:1500])


if __name__ == '__main__':
    main()

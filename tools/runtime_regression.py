#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终运行时回归：在 /tmp 副本中测试（仓库文件绝不修改）
- 资源用符号链接（images/ js/ css/ api/ 等目录）
- 被测 HTML 用真实拷贝 + 注入检测脚本
"""
import functools, http.server, json, os, re, shutil, socketserver, subprocess, sys, threading

SRC = "/Users/w/Desktop/Chinawheely 10.27"
TMP = "/tmp/cw_runtime_final"
PORT = 8891
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PAGES = ['index.html', 'booking.html', 'contact.html', '404.html', 'admin.html',
         'manage-order.html', 'juancheng.html', 'chongqing.html', 'xian.html',
         'prices.html', 'services.html', 'help.html', 'terms.html', 'thank-you.html',
         'seo-swot-analysis.html', 'batch_download.html', 'image_downloader.html',
         'beijing.html', 'shanghai.html']

INJECT = """
<script>
window.__errs=[];
window.addEventListener('error',function(e){window.__errs.push('JS:'+(e.message||''))});
window.addEventListener('unhandledrejection',function(e){window.__errs.push('REJ:'+String(e.reason).slice(0,60))});
setTimeout(function(){
 var o={};
 o.errs=window.__errs.slice(0,4);
 o.main=document.querySelectorAll('main').length;
 o.footer=document.querySelectorAll('footer').length;
 o.h1=document.querySelectorAll('h1').length;
 o.imgs=document.querySelectorAll('img').length;
 o.broken=0; Array.prototype.forEach.call(document.querySelectorAll('img'),function(im){if(im.complete&&im.naturalWidth===0)o.broken++;});
 o.of=document.documentElement.scrollWidth>window.innerWidth+2;
 o.text=(document.body.innerText||'').replace(/\\s+/g,' ').trim().length;
 o.h1txt=(document.querySelector('h1')||{}).textContent||'';
 document.title=JSON.stringify(o);
},2600);
</script>
"""


def setup():
    if os.path.exists(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    for name in os.listdir(SRC):
        s = os.path.join(SRC, name)
        d = os.path.join(TMP, name)
        if os.path.isdir(s):
            os.symlink(s, d)
        elif name.endswith('.html'):
            shutil.copy2(s, d)
        else:
            os.symlink(s, d)
    for pg in PAGES:
        p = os.path.join(TMP, pg)
        if os.path.exists(p) and not os.path.islink(p):
            s = open(p, encoding='utf-8').read()
            open(p, 'w', encoding='utf-8').write(s.replace('</body>', INJECT + '</body>'))


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
        return {'raw': m.group(1)[:120]}


def main():
    setup()
    Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=TMP)
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    bad = 0
    try:
        print('%-24s %-6s %-7s %-5s %-6s %-8s %s' % ('页面', 'main', 'footer', 'h1', 'img', 'text', '问题'))
        for pg in PAGES:
            r = run("http://127.0.0.1:%d/%s" % (PORT, pg))
            probs = []
            if r.get('errs'):
                probs.append('JS错误:' + str(r['errs'][:2]))
            if r.get('broken'):
                probs.append('坏图%d' % r['broken'])
            if r.get('of'):
                probs.append('横向溢出')
            if r.get('main') == 0:
                probs.append('无main')
            if (r.get('text') or 0) < 150:
                probs.append('内容过少(%s)' % r.get('text'))
            if probs:
                bad += 1
            print('%-24s %-6s %-7s %-5s %-6s %-8s %s' % (
                pg.replace('.html', ''), r.get('main'), r.get('footer'), r.get('h1'),
                '%s/%s' % (r.get('imgs'), r.get('broken')), r.get('text'),
                ('❌ ' + '; '.join(probs)) if probs else 'OK'))
    finally:
        httpd.shutdown()
        shutil.rmtree(TMP, ignore_errors=True)
    print('\n问题页 %d / %d' % (bad, len(PAGES)))
    print('仓库文件未被修改 ✓（测试在 /tmp 副本进行，副本已删除）')


if __name__ == '__main__':
    main()

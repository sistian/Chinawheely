#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 Chrome BarcodeDetector 解码两个收款二维码，核对收款账号"""
import functools, http.server, json, os, re, socketserver, subprocess, threading

ROOT = "/Users/w/Desktop/Chinawheely 10.27"
PORT = 8841
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PAGE = """<!doctype html><meta charset="utf-8">
<img id="a" src="images/pay-paypal-qr-clean.png">
<img id="b" src="images/pay-alipay-qr-clean.png">
<script>
(async function(){
  var out={};
  var det = ('BarcodeDetector' in window) ? new BarcodeDetector({formats:['qr_code']}) : null;
  out.hasDetector = !!det;
  async function dec(id){
    var im=document.getElementById(id);
    if(!det) { return 'NO_DETECTOR'; }
    if(!im.complete){ await new Promise(function(res){ im.onload=res; im.onerror=res; }); }
    await new Promise(function(res){ setTimeout(res, 800); });
    try{
      var bmp = await createImageBitmap(im);
      var r = await det.detect(bmp);
      return r.length? r[0].rawValue : 'NO_CODE_FOUND';
    }catch(e){ return 'ERR:'+String(e).slice(0,90); }
  }
  out.paypal = await dec('a');
  out.alipay = await dec('b');
  var pre=document.createElement('pre'); pre.id='qrout';
  pre.textContent=JSON.stringify(out);
  document.body.appendChild(pre);
  document.title = JSON.stringify(out);
})();
</script>
"""


def run(url):
    args = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=12000",
            "--window-size=1200,1200", "--dump-dom", url]
    p = subprocess.run(args, capture_output=True, text=True, timeout=120)
    m = re.search(r'<title>(.*?)</title>', p.stdout, re.S)
    if not m:
        return {'fatal': 'no title', 'stderr': p.stderr[-300:]}
    try:
        return json.loads(m.group(1).strip())
    except Exception:
        return {'raw': m.group(1)[:200]}


def main():
    page = os.path.join(ROOT, '_qr_check.html')
    open(page, 'w', encoding='utf-8').write(PAGE)
    Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        r = run("http://127.0.0.1:%d/_qr_check.html" % PORT)
        print(json.dumps(r, ensure_ascii=False, indent=1))
    finally:
        os.remove(page)
        httpd.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""联系表单提交链路测试（本地 harness，拦截 fetch 看 payload 与校验）"""
import functools, http.server, json, os, re, socketserver, subprocess, threading

ROOT = "/Users/w/Desktop/Chinawheely 10.27"
PORT = 8853
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

INJECT = r"""
<script>
window.__errs=[];
window.addEventListener('error',function(e){window.__errs.push(String(e.message));});
(function(){
 var _f=window.fetch; var __posts=[];
 window.fetch=function(u,o){
   if(o&&o.method==='POST'){ __posts.push({url:String(u),body:String(o.body||'')});
     return Promise.resolve({ok:true,status:200,json:function(){return Promise.resolve({ok:true,message:'sent'});},
       text:function(){return Promise.resolve('ok');}});}
   return _f.apply(this,arguments);
 };
 function setVal(id,v){var e=document.getElementById(id); if(!e)return; e.value=v;
   e.dispatchEvent(new Event('input',{bubbles:true})); e.dispatchEvent(new Event('change',{bubbles:true}));}
 var out={};
 setTimeout(function(){
  try{
   setVal('firstName','Probe'); setVal('lastName','User'); setVal('email','probe@example.com'); setVal('phone','+8615000000000');
   setVal('message','Test message from audit harness.');
   var f=document.querySelector('form');
   out.formAction=f?(f.getAttribute('action')||'(none)'):'NO_FORM';
   out.formMethod=f?(f.getAttribute('method')||'(get)'):'-';
   out.inputs=Array.prototype.map.call(document.querySelectorAll('input,select,textarea'),function(e){
     return e.name+(e.required?'*':'')+(e.type==='hidden'?'(hidden)':'');});
   // 空表单提交 → 应触发校验阻止
   var fm=document.querySelector('form');
   fm.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
   setTimeout(function(){
     out.postsAfterEmpty=__posts.length;
     out.emptyBlocked = __posts.length===0;
     // 必填校验消息
     var inv=document.querySelectorAll(':invalid');
     out.invalidCount=inv.length;
     out.invalidFirst=inv.length? (inv[0].name||inv[0].id||inv[0].tagName):'';
     // 正式提交
     setVal('firstName','Probe'); setVal('lastName','User'); setVal('email','probe@example.com'); setVal('phone','+8615000000000');
     setVal('message','Test message from audit harness.');
     fm.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
     setTimeout(function(){
       out.posts=__posts.length;
       out.postUrl=__posts.length?__posts[0].url:null;
       out.postBody=__posts.length?String(__posts[0].body).slice(0,400):null;
       out.errs=window.__errs;
       document.title=JSON.stringify(out);
     },900);
   },700);
  }catch(e){ document.title=JSON.stringify({fatal:String(e),errs:window.__errs}); }
 },1100);
})();
</script>
"""


def run(url):
    args = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=12000",
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
    for pg in ['contact.html']:
        fp = os.path.join(ROOT, pg)
        o = open(fp, encoding='utf-8').read()
        open(fp, 'w', encoding='utf-8').write(o.replace('</body>', INJECT + '</body>'))
        Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
        httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
        httpd.allow_reuse_address = True
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            r = run("http://127.0.0.1:%d/%s" % (PORT, pg))
            print('### ' + pg)
            print(json.dumps(r, ensure_ascii=False, indent=1))
        finally:
            open(fp, 'w', encoding='utf-8').write(o)
            httpd.shutdown()
            break


if __name__ == '__main__':
    main()

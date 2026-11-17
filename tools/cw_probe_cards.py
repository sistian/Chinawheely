#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针：读取首页城市卡片在真实浏览器中的 computed style 与几何尺寸。

用法： python3 tools/cw_probe_cards.py
"""
import json
import os
import re
import subprocess
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PROBE = """
<script>
window.addEventListener('load',function(){
 setTimeout(function(){
  var out=[];
  var cards=document.querySelectorAll('.city-card-wrapper');
  var vis=0, withimg=0;
  for(var i=0;i<cards.length;i++){
    if(!cards[i].classList.contains('hidden')) vis++;
    if(cards[i].querySelector('.city-card-bg img')) withimg++;
  }
  out.push('total='+cards.length+' visible='+vis+' withImg='+withimg);
  function r(el){ if(!el) return null; var b=el.getBoundingClientRect(); return [Math.round(b.x),Math.round(b.y),Math.round(b.width),Math.round(b.height)]; }
  function cs(el,p){ if(!el) return null; return getComputedStyle(el).getPropertyValue(p); }
  for(var i=0;i<3;i++){
    var w=cards[i]; if(!w) break;
    var card=w.querySelector('.city-card'), cap=w.querySelector('.city-card-caption'),
        nm=w.querySelector('.city-card-name'), cn=w.querySelector('.city-card-name-cn'),
        img=w.querySelector('.city-card-bg img');
    out.push('CARD'+i+' name='+(nm?nm.textContent:'?'));
    out.push(' cardRect='+JSON.stringify(r(card)));
    out.push(' imgRect='+JSON.stringify(r(img))+' nat='+(img?img.naturalWidth+'x'+img.naturalHeight:'-'));
    out.push(' capRect='+JSON.stringify(r(cap)));
    out.push(' capPos='+cs(cap,'position')+' align='+cs(cap,'align-items')+' just='+cs(cap,'justify-content')+' disp='+cs(cap,'display')+' dir='+cs(cap,'flex-direction'));
    out.push(' nmRect='+JSON.stringify(r(nm))+' disp='+cs(nm,'display')+' fs='+cs(nm,'font-size')+' lh='+cs(nm,'line-height'));
    out.push(' cnRect='+JSON.stringify(r(cn))+' disp='+cs(cn,'display')+' fs='+cs(cn,'font-size')+' txt='+(cn?cn.textContent:'-'));
    out.push(' overlap='+(nm&&cn? (nm.getBoundingClientRect().bottom > cn.getBoundingClientRect().top ? 'YES' : 'no'):'?'));
  }
  document.title='PROBE::'+out.join(' ;; ');
 },3000);
});
</script>
"""

def main():
    src = os.path.join(SITE, "index.html")
    tmp = os.path.join(SITE, "_probe_cards.html")
    h = open(src, encoding="utf-8").read()
    h = h.replace("</head>", PROBE + "</head>")
    open(tmp, "w", encoding="utf-8").write(h)
    try:
        url = "file://" + tmp.replace(" ", "%20")
        p = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--force-prefers-reduced-motion",
             "--virtual-time-budget=15000", "--window-size=1440,1200", "--dump-dom", url],
            capture_output=True, text=True, timeout=150)
        m = re.search(r"PROBE::([^<]*)", p.stdout)
        if not m:
            print("探针未回读成功")
            return 1
        out = os.path.join(SITE, "tools", "cw_probe_cards_out.txt")
        with open(out, "w", encoding="utf-8") as f:
            for line in m.group(1).split(";;"):
                f.write(line.strip() + "\n")
        print("已写入:", out)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return 0

if __name__ == "__main__":
    sys.exit(main())

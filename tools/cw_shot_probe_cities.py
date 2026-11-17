#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对「城市板块独立页」同时做：探针（几何）+ 截图（视觉），两者坐标一致。

用法： python3 tools/cw_shot_probe_cities.py [输出png]
"""
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
  var cards=document.querySelectorAll('.city-card-wrapper');
  var out=[];
  for(var i=0;i<3;i++){
    var w=cards[i]; if(!w) break;
    var card=w.querySelector('.city-card'), cap=w.querySelector('.city-card-caption'),
        nm=w.querySelector('.city-card-name'), cn=w.querySelector('.city-card-name-cn');
    function r(el){ if(!el) return null; var b=el.getBoundingClientRect(); return [Math.round(b.x),Math.round(b.y),Math.round(b.width),Math.round(b.height)]; }
    out.push('C'+i+' '+nm.textContent+'/'+cn.textContent+
      ' card='+JSON.stringify(r(card))+' cap='+JSON.stringify(r(cap))+
      ' nm='+JSON.stringify(r(nm))+' cn='+JSON.stringify(r(cn)));
  }
  document.title='PROBE::'+out.join(' ;; ');
 },2500);
});
</script>
"""


def main():
    out_png = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cw_shots/cities_probe.png"
    h = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    head = h[: h.find("</head>") + len("</head>")]
    i = h.find('<section class="section section-dark" id="cities">')
    j = h.find("</section>", i) + len("</section>")
    sec = h[i:j]
    tmp = os.path.join(SITE, "_shot_probe.html")
    page = (head.replace("</head>", PROBE + "</head>")
            + '<body style="padding-top:0">' + sec + '</body></html>')
    open(tmp, "w", encoding="utf-8").write(page)
    try:
        url = "file://" + tmp.replace(" ", "%20")
        p = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--force-prefers-reduced-motion",
             "--virtual-time-budget=12000", "--window-size=1440,1400", "--dump-dom", url],
            capture_output=True, text=True, timeout=150)
        m = re.search(r"PROBE::([^<]*)", p.stdout)
        print(m.group(1).replace(" ;; ", "\n") if m else "探针失败")
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--force-prefers-reduced-motion",
             "--hide-scrollbars", "--virtual-time-budget=12000",
             "--window-size=1440,1400", "--screenshot=" + out_png, url],
            capture_output=True, timeout=150)
        print("截图:", out_png)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""迁移前一致性检查：GitHub Pages vs Vercel 静态托管
逐项比对：HTTP 状态 / 关键元素 / 资源可达 / CSP 头
"""
import subprocess, re, urllib.request, urllib.error, sys

GH = "https://www.chinawheely.com"
VC = "https://chinawheely-backend-api.vercel.app"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PAGES = ["index.html", "beijing.html", "shanghai.html", "changchun.html",
         "taizhou_js.html", "yichun_hlj.html", "suzhou_ah.html", "fuzhou_jx.html",
         "yulin_sx.html", "booking.html", "manage-order.html", "prices.html",
         "sitemap.xml", "robots.txt", "404.html"]


def head(url, extra=None):
    req = urllib.request.Request(url, headers=extra or {
        "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except Exception as e:
        return 0, str(e).encode(), {}


print("=" * 78)
print("【1】HTTP 状态与体积对比")
print("=" * 78)
print(f"{'页面':22s} {'GitHub':>18s} {'Vercel':>18s}  一致")
bad = 0
for p in PAGES:
    gs, gb, _ = head(f"{GH}/{p}")
    vs, vb, _ = head(f"{VC}/{p}")
    same = "✅" if (gs == vs and len(gb) == len(vb)) else ("⚠ " if gs == vs else "❌")
    if same != "✅":
        bad += 1
    print(f"   {p:20s} {gs:>6d} {len(gb):>9d}B {vs:>6d} {len(vb):>9d}B  {same}")

print("\n" + "=" * 78)
print("【2】DOM 渲染一致性（Chrome headless，抽 4 页）")
print("=" * 78)
for p in ["index.html", "beijing.html", "taizhou_js.html", "booking.html"]:
    def dom(u, proxied):
        args = [CHROME, "--headless", "--disable-gpu", "--virtual-time-budget=6000", "--dump-dom"]
        # vercel.app 必须走本机代理（直连不通）；www.chinawheely.com 直连
        args += ["--proxy-server=http://127.0.0.1:7897"] if proxied else ["--no-proxy-server"]
        args.append(u)
        r = subprocess.run(args, capture_output=True, text=True, timeout=150)
        return r.stdout
    dg = dom(f"{GH}/{p}", False)
    dv = dom(f"{VC}/{p}", True)

    def sig(d):
        return (len(re.findall(r"<h1[\s>]", d, re.I)),
                len(re.findall(r"<h2[\s>]", d, re.I)),
                len(re.findall(r"<h3[\s>]", d, re.I)),
                len(re.findall(r"<img[\s>]", d, re.I)),
                len(re.findall(r"<a[\s>]", d, re.I)),
                len(re.findall(r"application/ld\+json", d, re.I)))
    sg, sv = sig(dg), sig(dv)
    ok = "✅" if sg == sv else "❌"
    if sg != sv:
        bad += 1
    print(f"   {p:18s} GH(H1,H2,H3,img,a,ld)={sg}")
    print(f"   {'':18s} VC(H1,H2,H3,img,a,ld)={sv}  {ok}")

print("\n" + "=" * 78)
print("【3】Vercel 响应头 vs GitHub Pages")
print("=" * 78)
_, _, gh_h = head(f"{GH}/index.html")
_, _, vc_h = head(f"{VC}/index.html")
for k in ["Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options",
          "Strict-Transport-Security", "Referrer-Policy", "Permissions-Policy"]:
    g = gh_h.get(k, "(无)")
    v = vc_h.get(k, "(无)")
    print(f"   {k:30s} GH: {g[:40]:42s} VC: {'有 ✅' if v != '(无)' else '无 ⚠'}")

print("\n" + "=" * 78)
print("【4】资源引用是否同源可达（Vercel 上的图片/CSS/JS）")
print("=" * 78)
_, vb, _ = head(f"{VC}/index.html")
html = vb.decode("utf-8", "ignore")
refs = re.findall(r'(?:src|href)=["\']([^"\']+\.(?:css|js|png|jpg|webp|svg|ico))', html)
print(f"   首页引用资源 {len(refs)} 个")
miss = []
for r in refs[:40]:
    u = r if r.startswith("http") else (VC + "/" + r.lstrip("./"))
    s, _, _ = head(u)
    if s != 200:
        miss.append((r, s))
print(f"   抽样 40 个，不可达 {len(miss)} 个")
for r, s in miss[:8]:
    print(f"      ❌ {s} {r}")

print("\n" + ("✅ 迁移一致性通过，可切 DNS" if bad == 0 and not miss else f"⚠ 有 {bad} 项差异 + {len(miss)} 个资源问题"))
sys.exit(0 if (bad == 0 and not miss) else 1)

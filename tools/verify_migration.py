#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""迁移状态检查：www.chinawheely.com 是否已切到 Vercel + 301 是否真实生效
退出码 0=已迁移完成且正常；1=未迁移或异常
"""
import socket, ssl, subprocess, sys, urllib.request, urllib.error, datetime

HOST = "www.chinawheely.com"
EXPECT_CNAME = "vercel-dns"          # Vercel CNAME 特征
GH_CNAME = "github.io"
REDIRECTS = [
    ("/beijing_detailed.html", "/beijing.html"),
    ("/erdos.html", "/eerduosi.html"),
    ("/hulunbeier.html", "/eerduosi.html"),
    ("/jdz.html", "/jingdezhen.html"),
    ("/jinzhou_ln.html", "/jinzhou.html"),
    ("/jl.html", "/jilin.html"),
    ("/juncheng.html", "/yuncheng.html"),
    ("/kelamayi.html", "/karamay.html"),
    ("/suzhou-jiangsu.html", "/suzhou.html"),
    ("/taizhou_zj.html", "/taizhou.html"),
    ("/wulumuqi.html", "/urumqi.html"),
    ("/yan_an.html", "/yanan.html"),
    ("/yichun-heilongjiang.html", "/yichun_hlj.html"),
    ("/yichun_jx.html", "/yichun.html"),
]


def resolve(host):
    out = subprocess.run(["dig", "+short", "CNAME", host, "@223.5.5.5"],
                          capture_output=True, text=True, timeout=30).stdout.strip()
    ips = subprocess.run(["dig", "+short", "A", host, "@223.5.5.5"],
                          capture_output=True, text=True, timeout=30).stdout.strip().split()
    return out, ips


def http(url, method="GET"):
    req = urllib.request.Request(url, method=method,
                                 headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, r.geturl(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, url, dict(e.headers)
    except Exception as e:
        return 0, str(e), {}


print("=" * 70)
print(f"迁移状态检查  {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
print("=" * 70)

cname, ips = resolve(HOST)
print(f"\n【DNS】{HOST}")
print(f"   CNAME = {cname or '(无)'}")
print(f"   A     = {' '.join(ips) or '(无)'}")
on_gh = GH_CNAME in cname or any(i.startswith("185.199.") for i in ips)
on_vc = EXPECT_CNAME in cname or any(i in ("76.76.21.21", "216.198.79.1", "64.29.17.1") for i in ips)
print(f"   指向 GitHub Pages : {'是' if on_gh else '否'}")
print(f"   指向 Vercel       : {'是' if on_vc else '否'}")

print("\n【TLS 证书】")
try:
    ctx = ssl.create_default_context()
    with socket.create_connection((HOST, 443), timeout=15) as sock:
        with ctx.wrap_socket(sock, server_hostname=HOST) as ss:
            cert = ss.getpeercert()
            print(f"   签发给 = {dict(x[0] for x in cert.get('subject', []))}")
            print(f"   有效期 = {cert.get('notAfter')}")
            sans = [v for k, v in cert.get('subjectAltName', []) if k == 'DNS']
            print(f"   SAN    = {', '.join(sans[:5])}")
            vc_cert = any("vercel" in str(v).lower() or "inc" in str(v).lower() for v in sans) or \
                      any("vercel" in str(v).lower() for v in cert.get('issuer', ()))
            print(f"   Vercel 签发 = {'✅' if vc_cert else '⚠ 非 Vercel'}")
except Exception as e:
    print(f"   ❌ {e}")

print("\n【301 重定向】")
bad = []
for src, dst in REDIRECTS:
    st, final, h = http(f"https://{HOST}{src}")
    loc = h.get("Location", "")
    good = (st == 301 and loc.replace("https://" + HOST, "").rstrip("/") == dst)
    if not good:
        bad.append((src, st, loc))
    print(f"   {'✅' if good else '❌'} {src:30s} http={st} → {loc.replace('https://' + HOST, '') or '(无)'}")
print(f"   不合格 {len(bad)} / {len(REDIRECTS)}")

print("\n【站点可用性】")
for p in ["/", "/index.html", "/beijing.html", "/sitemap.xml", "/robots.txt"]:
    st, final, h = http(f"https://{HOST}{p}")
    print(f"   {p:16s} http={st}  最终URL={final}")

print("\n【关键安全响应头（应只有 Vercel 才有）】")
_, _, h = http(f"https://{HOST}/index.html")
for k in ["Content-Security-Policy", "X-Frame-Options", "Strict-Transport-Security"]:
    print(f"   {k:30s} {'✅' if k in h else '❌ 缺失'}")

done = on_vc and not bad
print("\n" + ("✅ 迁移已完成：www 已指向 Vercel，14 条 301 全部生效"
              if done else "⏳ 尚未完成迁移（DNS 仍指向 GitHub Pages 或 301 未生效）"))
sys.exit(0 if done else 1)

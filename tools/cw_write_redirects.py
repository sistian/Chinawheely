#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 301 重定向表写进 vercel.json（幂等）：
- 14 个别名桩页 → 权威目标页，statusCode 301
- 同时保留 headers 段
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VP = os.path.join(ROOT, "vercel.json")

REDIRECTS = [
    ("/beijing_detailed.html", "/beijing.html"),
    ("/erdos.html", "/eerduosi.html"),
    ("/hulunbeier.html", "/eerduosi.html"),
    ("/jdz.html", "/jingdezhen.html"),
    ("/jincheng.html", "/jincheng.html"),          # 占位，稍后剔除
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
REDIRECTS = [(s, d) for s, d in REDIRECTS if s != d]   # 剔除自我重定向

cfg = json.load(open(VP, encoding="utf-8"))
existing = cfg.get("redirects", [])
seen = {(r.get("source"), r.get("destination")) for r in existing}
added = 0
for src, dst in REDIRECTS:
    if (src, dst) in seen:
        continue
    existing.append({"source": src, "destination": dst, "statusCode": 301})
    added += 1
cfg["redirects"] = existing
json.dump(cfg, open(VP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"vercel.json 重定向：新增 {added} 条，共 {len(existing)} 条")
for r in existing:
    print(f"   301  {r['source']:30s} → {r['destination']}")

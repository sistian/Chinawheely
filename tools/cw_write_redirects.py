#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 301 重定向表写进 vercel.json（幂等）：
- 14 个别名桩页 → 权威正牌页，statusCode 301
- 主题页合并（best-time 23 + tea-culture 10）→ 城市页锚点
- 同时保留 headers 段（CSP / X-Frame-Options / HSTS …）
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VP = os.path.join(ROOT, "vercel.json")
MERGE_PLAN = os.path.join(ROOT, "tools", "theme_merge_plan.json")

# 14 个别名桩页（正文 <1000 字符的 H1="This page has moved" 页）
ALIAS_REDIRECTS = [
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


def build_plan():
    plan = dict(ALIAS_REDIRECTS)
    if os.path.exists(MERGE_PLAN):
        for slug, target in json.load(open(MERGE_PLAN, encoding="utf-8")).items():
            plan[f"/{slug}.html"] = target
    return plan


def main():
    plan = build_plan()
    cfg = json.load(open(VP, encoding="utf-8"))
    cfg["redirects"] = [
        {"source": s, "destination": d, "statusCode": 301}
        for s, d in sorted(plan.items())
    ]
    json.dump(cfg, open(VP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"vercel.json redirects = {len(cfg['redirects'])} 条（别名 {len(ALIAS_REDIRECTS)} + 主题合并 {len(plan) - len(ALIAS_REDIRECTS)}）")
    for r in cfg["redirects"]:
        print(f"   301  {r['source']:36s} → {r['destination']}")
    # 自检
    srcs = [r["source"] for r in cfg["redirects"]]
    assert len(srcs) == len(set(srcs)), "source 有重复"
    for r in cfg["redirects"]:
        assert r["source"] != r["destination"], f"自我重定向: {r}"
    print("   自检通过：无重复 source、无自我重定向")


if __name__ == "__main__":
    main()

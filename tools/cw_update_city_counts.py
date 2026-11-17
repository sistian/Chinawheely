#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""城市数文案校正：333 → 359（只改「城市数量」语境的 333，避开 #333 颜色 / USCC / 面积）
幂等：改过就不会再改
"""
import os, re, sys

REPO = "/Users/w/Desktop/Chinawheely 10.27"
OLD, NEW = 333, 359

# (正则, 说明) —— 必须带上下文，避免误伤 color:#333 / 证件号 / 面积
RULES = [
    (r"Browse all 333 cities we serve", "Browse all %d cities we serve" % NEW),
    (r"333 cities, licensed professional drivers", "%d cities, licensed professional drivers" % NEW),
    (r"private car service across 333 cities in China", "private car service across %d cities in China" % NEW),
    (r"across 333 cities in China", "across %d cities in China" % NEW),
    (r"in 333 cities in China", "in %d cities in China" % NEW),
    (r"333 cities in China", "%d cities in China" % NEW),
    (r"333 cities covered", "%d cities covered" % NEW),
    (r"333 Cities Covered", "%d Cities Covered" % NEW),
    (r"All 333 Cities", "All %d Cities" % NEW),
    (r">333</div>", ">%d</div>" % NEW),
    (r"all 333 cities", "all %d cities" % NEW),
    (r"346 cities on the platform", "%d cities on the platform" % NEW),
    (r"333 cities on the platform", "%d cities on the platform" % NEW),
    (r"343 cities", "%d cities" % NEW),
    (r"licensed professional driver in 333 cities", "licensed professional driver in %d cities" % NEW),
    (r"Private Car Service in 333 China Cities", "Private Car Service in %d China Cities" % NEW),
    (r"toc-private-car-service-in-333-china-cities", "toc-private-car-service-in-%d-china-cities" % NEW),
    (r"across all 333 China cities", "across all %d China cities" % NEW),
    (r"Beijing, Shanghai, Guangzhou, Shenzhen &amp; 333 cities", "Beijing, Shanghai, Guangzhou, Shenzhen &amp; %d cities" % NEW),
    (r"in 333 China cities", "in %d China cities" % NEW),
    (r"333 China cities", "%d China cities" % NEW),
    (r"333 destinations", "%d destinations" % NEW),
    (r"Browse All 333 China Cities", "Browse All %d China Cities" % NEW),
    (r"All 333 cities available across China", "All %d cities available across China" % NEW),
    (r"in 333 Chinese cities", "in %d Chinese cities" % NEW),
    (r"in 333 cities", "in %d cities" % NEW),
    (r"333 cities to deliver", "%d cities to deliver" % NEW),
    (r"333 cities\.", "%d cities." % NEW),
]

SKIP_DIRS = {".git", "node_modules", "tools", "api", "images", "pricing", "seo_assets"}


def main():
    targets = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith((".html", ".js", ".xml", ".md")):
                targets.append(os.path.join(root, f))
    changed = []
    total = 0
    for p in targets:
        try:
            t = open(p, encoding="utf-8").read()
        except Exception:
            continue
        orig = t
        for pat, rep in RULES:
            t = re.sub(pat, rep, t)
        if t != orig:
            n = sum(orig.count(x) for x in ["333 cities", "333 Cities", "All 333", ">333<", "346 cities", "343 cities"])
            open(p, "w", encoding="utf-8").write(t)
            changed.append((os.path.relpath(p, REPO), n))
            total += n
    print("改动文件 %d，替换处约 %d" % (len(changed), total))
    for f, n in sorted(changed, key=lambda x: -x[1])[:15]:
        print("  %-42s %d" % (f, n))
    # 残留检查
    left = []
    for p in targets:
        try:
            t = open(p, encoding="utf-8").read()
        except Exception:
            continue
        for m in re.finditer(r".{0,45}333.{0,35}", t):
            s = m.group(0)
            if any(k in s for k in ["color:#333", "color: #333", "USCC", "91440300", "km²", "km2", "area of 333", "=333", "333,333"]):
                continue
            left.append((os.path.relpath(p, REPO), s.strip()[:110]))
    print("\n剩余待人工确认的 333（%d 处）：" % len(left))
    seen = {}
    for f, s in left:
        seen.setdefault(s, []).append(f)
    for s, fs in sorted(seen.items(), key=lambda x: -len(x[1]))[:25]:
        print("  %-4d %s" % (len(fs), s))


if __name__ == "__main__":
    main()

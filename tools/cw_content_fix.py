#!/usr/bin/env python3
"""
内容缺陷修复（模板占位符未替换）
  A. 147 个城市页 keywords 中的 "Local airport transfer"
     - 有真实机场代码的 → 换成 "{CODE} airport transfer"
     - 无机场的次要城市 → 直接删除该关键词（第 1 个关键词已是 "{City} airport transfer"，不丢信息）
  B. beijing.html / beijing-tea-culture.html 中的
     "Local"(机场名/街区名)、"Beijing Attraction"、"Beijing STYLE"、"Beijing Professional"
     等未替换占位符
幂等：可重复执行。
"""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cw_common import ROOT, read, write, html_files

report = {"kw_fixed": [], "kw_removed": [], "text_fixed": [], "notes": []}

# ---------- A. keywords 里的 "Local airport transfer" ----------
CODE_MAP = {
    "beihai.html": "BHY", "beijing.html": "PEK", "fuzhou_jx.html": "FOC",
    "huainan.html": "HFE", "huangshan.html": "TXN", "hulunbuir.html": "HLD",
    "jining.html": "JNG", "linyi.html": "LYI", "nanning.html": "NNG",
    "wuxi.html": "WUX", "yantai.html": "YNT", "yongxi.html": "NNG",
}

def fix_keywords():
    for f in html_files():
        p = os.path.join(ROOT, f)
        s = read(p)
        if "Local airport transfer" not in s:
            continue
        m = re.search(r'(<meta name="keywords" content=")([^"]*)(")', s)
        if not m:
            report["notes"].append(f"{f}: 无 keywords meta")
            continue
        kws = [k.strip() for k in m.group(2).split(",") if k.strip()]
        if "Local airport transfer" not in kws:
            continue
        code = CODE_MAP.get(f)
        if code:
            kws = [f"{code} airport transfer" if k == "Local airport transfer" else k for k in kws]
            report["kw_fixed"].append(f"{f} → {code} airport transfer")
        else:
            kws = [k for k in kws if k != "Local airport transfer"]
            report["kw_removed"].append(f)
        new = m.group(1) + ", ".join(kws) + m.group(3)
        s2 = s[:m.start()] + new + s[m.end():]
        if s2 != s:
            write(p, s2)

# ---------- B. 北京两页的占位符 ----------
# (文件, 原文, 替换)
TEXT_FIXES = [
    # ---- beijing.html：Local = 北京首都机场 PEK ----
    ("beijing.html", "Local Airport → City Center", "Capital Airport (PEK) → City Center"),
    ("beijing.html", "Local Daxing → City Center", "Daxing Airport (PKX) → City Center"),
    ("beijing.html", "Local & PKX to downtown", "PEK & PKX to downtown"),
    ("beijing.html", "Local is China's busiest international gateway",
     "Beijing Capital Airport (PEK) is China's busiest international gateway"),
    ("beijing.html", "from Local or PKX to any Beijing hotel",
     "from PEK or PKX to any Beijing hotel"),
    ("beijing.html", "Local airport pickup", "PEK airport pickup"),
    ("beijing.html", "Local Airport Transfer", "Beijing Capital Airport Transfer"),
    ("beijing.html", "27 km to Beijing Attraction", "27 km to the Forbidden City"),
    ("beijing.html", "Direct private transfer from Local or PKX to the Beijing Attraction",
     "Direct private transfer from PEK or PKX to the Forbidden City"),
    ("beijing.html", "Beijing Professional licensed driver", "Beijing professional licensed driver"),
    ("beijing.html", "Beijing Professional driver", "Beijing professional driver"),
    # ---- 北京茶文化：Local = 大栅栏 / 茶馆名 ----
    ("beijing.html", "Local (老舍茶馆)", "Lao She Teahouse (老舍茶馆)"),
    ("beijing.html", "Local, 3 Local East Street, Dongcheng District",
     "Lao She Teahouse, 3 Dashilan East Street, Xicheng District"),
    ("beijing.html", "Local Tea Street (大栅栏茶街)", "Dashilan Tea Street (大栅栏茶街)"),
    ("beijing.html", "Local, Xicheng District", "Dashilan, Xicheng District"),
    ("beijing.html", "The historic Local area near Local",
     "The historic Dashilan area near Dashilan"),
    ("beijing.html", "Various teahouses citywide near Local and Local",
     "Various teahouses citywide near Dashilan and Wangfujing"),
    ("beijing.html", "Wangfujing and Local tea streets", "Wangfujing and Dashilan tea streets"),
    ("beijing.html", "since 1989 near Local", "since 1989 near Dashilan"),
    # ---- beijing-tea-culture.html ----
    ("beijing-tea-culture.html",
     "from authentic pu-erh teahouses near Local to traditional Local with evening Peking opera",
     "from authentic pu-erh teahouses near Dashilan to traditional teahouses with evening Peking opera"),
    ("beijing-tea-culture.html", "Local Tea Street", "Dashilan Tea Street"),
    ("beijing-tea-culture.html", "<strong>Local</strong> area = historic tea district",
     "<strong>Dashilan</strong> area = historic tea district"),
    ("beijing-tea-culture.html", "Traditional teahouses near Local offer nightly shows",
     "Traditional teahouses near Dashilan offer nightly shows"),
    ("beijing-tea-culture.html", "Try at:</strong> Local, street-side teahouses",
     "Try at:</strong> Dashilan, street-side teahouses"),
    ("beijing-tea-culture.html", "Try at:</strong> Local, upscale teahouses",
     "Try at:</strong> Dashilan, upscale teahouses"),
    ("beijing-tea-culture.html", "Try at:</strong> Local, historic teahouses",
     "Try at:</strong> Dashilan, historic teahouses"),
    ("beijing-tea-culture.html", "both historic pharmacies-tea shops near Local",
     "both historic pharmacies-tea shops near Dashilan"),
    ("beijing-tea-culture.html", "Historic tea shops on Local", "Historic tea shops on Dashilan"),
    ("beijing-tea-culture.html", "Local (老舍茶馆)", "Lao She Teahouse (老舍茶馆)"),
    ("beijing-tea-culture.html", "3 Local East Street", "3 Dashilan East Street"),
    ("beijing-tea-culture.html", "The historic Local area near Local",
     "The historic Dashilan area near Dashilan"),
    ("beijing-tea-culture.html", "Visit Local for the full experience",
     "Visit Dashilan for the full experience"),
    ("beijing-tea-culture.html", "Go to Local in the afternoon", "Go to Dashilan in the afternoon"),
    ("beijing-tea-culture.html", "<h4>Local Street</h4>", "<h4>Dashilan Street</h4>"),
    ("beijing-tea-culture.html", "duck into Local's tea shops", "duck into Dashilan's tea shops"),
    ("beijing-tea-culture.html", "Combine with:</strong> Local evening show",
     "Combine with:</strong> Dashilan evening show"),
    ("beijing-tea-culture.html", "from Local's historic shops", "from Dashilan's historic shops"),
    ("beijing-tea-culture.html", "Beijing STYLE buildings", "Beijing-style courtyard buildings"),
    ("beijing-tea-culture.html", "from Beijing Tea Culture Attraction to reach the historic Local area",
     "from the Beijing Tea Culture Attraction to reach the historic Dashilan area"),
    # ---- beijing.html：第二个占位符 "Beijing Attraction"（按上下文还原真实景点）----
    ("beijing.html", "city tours, and Beijing Attraction excursions",
     "city tours, and Forbidden City excursions"),
    ("beijing.html", '"name": "Beijing Attraction Day Trip", "description": "Private transfer to Beijing Attraction"',
     '"name": "Forbidden City Day Trip", "description": "Private transfer to the Forbidden City"'),
    ("beijing.html", "home to the Beijing Attraction and the Beijing Attraction",
     "home to the Forbidden City and the Great Wall"),
    ("beijing.html", "Beijing → Beijing Attraction (Mutianyu)",
     "Beijing → Great Wall (Mutianyu)"),
    ("beijing.html",
     "Visit the Beijing Attraction, Beijing Attraction Square, Beijing Attraction, and Beijing Attraction in one day",
     "Visit the Forbidden City, Tiananmen Square, the Temple of Heaven, and the Great Wall in one day"),
    ("beijing.html", "46 km to Beijing Attraction", "46 km to the Forbidden City"),
    ("beijing.html", "30 min to Beijing Attraction", "30 min to the Forbidden City"),
    ("beijing.html", "25 min to Beijing Attraction", "25 min to the Forbidden City"),
    ("beijing.html", "10 min to Beijing Attraction", "10 min to Tiananmen Square"),
    ("beijing.html", "Badaling Beijing Attraction", "Badaling Great Wall"),
    ("beijing.html", "Beijing Roast Duck (Beijing Attraction)", "Beijing Roast Duck (Quanjude)"),
    ("beijing.html", "Beijing Attraction Masks", "Beijing Opera Masks"),
    ("beijing.html", "🎭 Beijing Attraction (Jingju)", "🎭 Beijing Opera (Jingju)"),
    ("beijing.html", "Beijing Attraction combines singing", "Beijing Opera combines singing"),
    ("beijing.html", "Beat the Crowds at the Beijing Attraction",
     "Beat the Crowds at the Forbidden City"),
    ("beijing.html", "Book the Beijing Attraction a Week Ahead",
     "Book the Forbidden City a Week Ahead"),
    ("beijing.html", "Use a Private Car for the Beijing Attraction",
     "Use a Private Car for the Great Wall"),
    # Square 变体必须先于通用变体替换
    ("beijing.html", "🚗 Beijing Airport Transfer to Beijing Attraction Square",
     "🚗 Beijing Airport Transfer to Tiananmen Square"),
    ("beijing.html", "Fixed-price transfer from Beijing airport to Beijing Attraction and nearby landmarks",
     "Fixed-price transfer from Beijing airport to Tiananmen Square and nearby landmarks"),
    ("beijing.html", "Walk straight into the Beijing Attraction.",
     "Walk straight into Tiananmen Square."),
    ("beijing.html", "🚗 Beijing Airport Transfer to Beijing Attraction</h4>",
     "🚗 Beijing Airport Transfer to the Forbidden City</h4>"),
    ("beijing.html", "Mutianyu Beijing Attraction tour · Beijing Attraction visit",
     "Mutianyu Great Wall tour · Forbidden City visit"),
    ("beijing.html", '"name": "Beijing Attraction Day Trip"',
     '"name": "Forbidden City Day Trip"'),
    ("beijing.html", '"description": "Private transfer to Beijing Attraction"',
     '"description": "Private transfer to the Forbidden City"'),
]

def fix_text():
    by_file = {}
    for f, old, new in TEXT_FIXES:
        by_file.setdefault(f, []).append((old, new))
    for f, pairs in by_file.items():
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            report["notes"].append(f"{f} 不存在")
            continue
        s = read(p)
        hit = 0
        for old, new in pairs:
            if old in s:
                s = s.replace(old, new)
                hit += 1
                report["text_fixed"].append(f"{f}: {old[:48]}")
        if hit:
            write(p, s)

if __name__ == "__main__":
    fix_keywords()
    fix_text()
    print(json.dumps({
        "kw_replaced_with_code": len(report["kw_fixed"]),
        "kw_removed": len(report["kw_removed"]),
        "text_placeholders_fixed": len(report["text_fixed"]),
        "notes": report["notes"],
    }, ensure_ascii=False, indent=2))

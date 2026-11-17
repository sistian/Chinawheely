#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 30 个缺口城市接入站点：
 1) cities.html —— 按省份插入城市条目 + 更新计数 + 重建 JSON-LD ItemList
 2) sitemap.xml —— 加入新页面 URL
幂等：已存在则跳过
"""
import json, os, re, datetime

REPO = "/Users/w/Desktop/Chinawheely 10.27"
SITE = "https://www.chinawheely.com"

# slug, 英文名, 中文名, 省份英文, 省份id
CITIES = [
    ("yili", "Ili", "伊犁哈萨克自治州", "Xinjiang", "xinjiang"),
    ("kizilsu", "Kizilsu", "克孜勒苏柯尔克孜自治州", "Xinjiang", "xinjiang"),
    ("bortala", "Bortala", "博尔塔拉蒙古自治州", "Xinjiang", "xinjiang"),
    ("tacheng", "Tacheng", "塔城地区", "Xinjiang", "xinjiang"),
    ("bayingolin", "Bayingolin", "巴音郭楞蒙古自治州", "Xinjiang", "xinjiang"),
    ("changji", "Changji", "昌吉回族自治州", "Xinjiang", "xinjiang"),
    ("aksu", "Aksu", "阿克苏地区", "Xinjiang", "xinjiang"),
    ("altay", "Altay", "阿勒泰地区", "Xinjiang", "xinjiang"),
    ("daxingan", "Daxinganling", "大兴安岭地区", "Heilongjiang", "heilongjiang"),
    ("dehong", "Dehong", "德宏傣族景颇族自治州", "Yunnan", "yunnan"),
    ("nujiang", "Nujiang", "怒江傈僳族自治州", "Yunnan", "yunnan"),
    ("chuxiong", "Chuxiong", "楚雄彝族自治州", "Yunnan", "yunnan"),
    ("xishuangbanna", "Xishuangbanna", "西双版纳傣族自治州", "Yunnan", "yunnan"),
    ("diqing", "Diqing", "迪庆藏族自治州", "Yunnan", "yunnan"),
    ("enshi", "Enshi", "恩施土家族苗族自治州", "Hubei", "hubei"),
    ("guoluo", "Guoluo", "果洛藏族自治州", "Qinghai", "qinghai"),
    ("haibei", "Haibei", "海北藏族自治州", "Qinghai", "qinghai"),
    ("hainan_qh", "Hainan", "海南藏族自治州", "Qinghai", "qinghai"),
    ("haixi", "Haixi", "海西蒙古族藏族自治州", "Qinghai", "qinghai"),
    ("yushu", "Yushu", "玉树藏族自治州", "Qinghai", "qinghai"),
    ("huangnan", "Huangnan", "黄南藏族自治州", "Qinghai", "qinghai"),
    ("ganzi", "Ganzi", "甘孜藏族自治州", "Sichuan", "sichuan"),
    ("aba", "Aba", "阿坝藏族羌族自治州", "Sichuan", "sichuan"),
    ("xilingol", "Xilingol", "锡林郭勒盟", "Inner Mongolia", "inner-mongolia"),
    ("alxa", "Alxa", "阿拉善盟", "Inner Mongolia", "inner-mongolia"),
    ("ali", "Ali", "阿里地区", "Tibet", "tibet"),
    ("qiandongnan", "Qiandongnan", "黔东南苗族侗族自治州", "Guizhou", "guizhou"),
    ("qiannan", "Qiannan", "黔南布依族苗族自治州", "Guizhou", "guizhou"),
    ("qianxinan", "Qianxinan", "黔西南布依族苗族自治州", "Guizhou", "guizhou"),
    ("jian_jx", "Ji'an", "吉安市", "Jiangxi", "jiangxi"),
]

def read(p):
    return open(p, encoding="utf-8").read()

def write(p, t):
    open(p, "w", encoding="utf-8").write(t)

def sec_bounds(h, sec_id):
    i = h.find('id="prov-%s"' % sec_id)
    if i < 0:
        return None
    start = h.rfind("<section", 0, i)
    end = h.find("</section>", i)
    return start, end

def insert_city(h, sec_id, slug, en, cn):
    b = sec_bounds(h, sec_id)
    if not b:
        return h, False
    start, end = b
    seg = h[start:end]
    if ('href="%s.html"' % slug) in seg:
        return h, False
    li = '      <li><a href="%s.html"><span class="cname">%s</span><span class="cen">%s</span></a></li>\n' % (slug, cn, en)
    # 该省现有条目按英文名排序，插入到正确位置
    items = list(re.finditer(r'<li><a href="([a-z0-9_]+)\.html"><span class="cname">[^<]*</span><span class="cen">([^<]*)</span></a></li>\n', seg))
    pos = None
    for m in items:
        if m.group(2).lower() > en.lower():
            pos = m.start()
            break
    if pos is None:
        if items:
            pos = items[-1].end()
        else:
            pos = seg.find("</ul>")
    new_seg = seg[:pos] + li + seg[pos:]
    return h[:start] + new_seg + h[end:], True

def main():
    # ---------- cities.html ----------
    p = os.path.join(REPO, "cities.html")
    h = read(p)
    added = []
    for slug, en, cn, prov, sec in CITIES:
        h, ok = insert_city(h, sec, slug, en, cn)
        if ok:
            added.append(slug)
    # 计数：统计实际城市链接
    n_cities = len(re.findall(r'<li><a href="[a-z0-9_]+\.html"><span class="cname">', h))
    h = re.sub(r"All \d+ Cities in China", "All %d Cities in China" % n_cities, h)
    h = re.sub(r"All \d+ Cities", "All %d Cities" % n_cities, h)
    # JSON-LD ItemList 重建
    items = []
    for m in re.finditer(r'<li><a href="([a-z0-9_]+)\.html"><span class="cname">([^<]*)</span><span class="cen">([^<]*)</span></a></li>', h):
        items.append((m.group(1), m.group(3)))
    il = ", ".join('{"@type": "ListItem", "position": %d, "name": "%s", "url": "%s/%s.html"}' % (i, en, SITE, s)
                   for i, (s, en) in enumerate(items, 1))
    def repl_il(m):
        return m.group(1) + "[" + il + "]" + m.group(3)
    h = re.sub(r'(\{"@context": "https://schema.org", "@type": "ItemList", "itemListElement": )\[.*?\](\})',
               repl_il, h, count=1, flags=re.S)
    write(p, h)
    print("cities.html: 新增 %d 城，城市链接总数 %d" % (len(added), n_cities))

    # ---------- sitemap ----------
    sp = os.path.join(REPO, "sitemap.xml")
    s = read(sp)
    today = datetime.date.today().isoformat()
    add_s = []
    for slug, en, cn, prov, sec in CITIES:
        if ("%s/%s.html" % (SITE, slug)) in s:
            continue
        add_s.append("  <url>\n    <loc>%s/%s.html</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>\n" % (SITE, slug, today))
    if add_s:
        s = s.replace("</urlset>", "".join(add_s) + "</urlset>")
        write(sp, s)
    print("sitemap.xml: 新增 %d 条" % len(add_s))

if __name__ == "__main__":
    main()

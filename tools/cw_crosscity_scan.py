#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站串城扫描：检测城市页里出现的其他城市专属地标/商圈。
思路：把「城市专属地标词 → 归属城市」建表，检查每个城市页是否出现了不属于自己城市的词。
只报「独占型」地标（不会同时是两个城市共同拥有的），避免误报。"""
import os, re, json, sys, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 城市专属地标 → 归属城市 slug。必须是「独占」的（某地名只属于一个城市）
LANDMARKS = {
    # 上海
    "the Bund": "shanghai", "Nanjing Road": "shanghai", "Nanjing East Road": "shanghai",
    "Lujiazui": "shanghai", "Yu Garden": "shanghai", "Jing'an Temple": "shanghai",
    "Xujiahui": "shanghai", "Zhujiajiao": "shanghai", "Oriental Pearl": "shanghai",
    "Pudong": "shanghai", "French Concession": "shanghai", "People's Square": "shanghai",
    # 北京
    "Forbidden City": "beijing", "Tiananmen": "beijing", "Great Wall": "beijing",
    "Summer Palace": "beijing", "Temple of Heaven": "beijing", "Wangfujing": "beijing",
    "Sanlitun": "beijing", "Hutong": "beijing", "Badaling": "beijing",
    "Mutianyu": "beijing", " Lama Temple": "beijing",
    # 广州
    "Canton Tower": "guangzhou", "Chen Clan Academy": "guangzhou",
    "Shangxiajiu": "guangzhou", "Beijing Road": "guangzhou",
    # 深圳
    "Window of the World": "shenzhen", "OCT": "shenzhen", "Dameisha": "shenzhen",
    # 成都
    "Jinli": "chengdu", "Wuhou Shrine": "chengdu", "Chunxi Road": "chengdu",
    "Du Fu Thatched Cottage": "chengdu", "Dujiangyan": "chengdu",
    "Giant Panda Base": "chengdu", "People's Park": "chengdu",
    # 西安
    "Terracotta Army": "xian", "Big Wild Goose Pagoda": "xian",
    "Muslim Quarter": "xian", "Xi'an City Wall": "xian", "Bell Tower": "xian",
    # 杭州
    "West Lake": "hangzhou", "Lingyin Temple": "hangzhou", "Xixi": "hangzhou",
    # 南京
    "Nanjing": "nanjing", "Zhongshan Ling": "nanjing", "Xuanwu Lake": "nanjing",
    "Confucius Temple": "nanjing", "Sun Yat-sen Mausoleum": "nanjing",
    # 重庆
    "Jiefangbei": "chongqing", "Hongya Cave": "chongqing", "Dazu": "chongqing",
    # 苏州
    "Jinji Lake": "suzhou", "Humble Administrator's Garden": "suzhou",
    "Pingjiang Road": "suzhou", "Tongli": "suzhou", "Zhouzhuang": "suzhou",
    # 杭州/绍兴
    "Lu Xun": "shaoxing",
    # 青岛
    "Badaguan": "qingdao", "Tsingtao": "qingdao", "Laoshan": "qingdao",
    # 长沙
    "Yuelu": "changsha", "Orange Isle": "changsha", "Tianxin": "changsha",
    # 桂林
    "Elephant Trunk Hill": "guilin", "Li River": "guilin", "Reed Flute Cave": "guilin",
    # 洛阳
    "Longmen Grottoes": "luoyang", "White Horse Temple": "luoyang",
    # 敦煌
    "Mogao Caves": "dunhuang", "Crescent Lake": "dunhuang",
    # 哈尔滨
    "Central Street": "harbin", "St. Sophia": "harbin", "Ice and Snow World": "harbin",
    # 三亚
    "Yalong Bay": "sanya", "Tianya Haijiao": "sanya", "Duty Free": "sanya",
    # 乌镇
    "Wuzhen": "wuzhen", "Xizha": "wuzhen",
    # 无锡
    "Lingshan": "wuxi", "Taihu": "wuxi",
    # 福州
    "Three Lanes": "fuzhou", "Yantai Mountain": "fuzhou", "Shangxiahang": "fuzhou",
    # 郑州
    "Henan Museum": "zhengzhou", "Erqi Memorial": "zhengzhou",
    # 天津
    "Five Great Avenues": "tianjin", "Italian Style": "tianjin", "Haihe": "tianjin",
    # 太原
    "Jinci": "taiyuan", "Twin Pagoda": "taiyuan",
    # 宁波
    "Tianyi Pavilion": "ningbo", "Moon Lake": "ningbo", "Old Bund": "ningbo",
    # 温州
    "Wuma Street": "wenzhou", "Yandang Mountain": "wenzhou",
    # 南通（本次核实）
    "Wenfeng Dashijie": "nantong", "Nanda Street": "nantong",
    # 烟台（本次核实）
    "Zhuhua Shopping Center": "yantai", "Zhifu": "yantai",
}

files = [f for f in sorted(os.listdir(BASE))
         if f.endswith(".html") and not f.startswith("_")]

hits = collections.defaultdict(list)
for fn in files:
    slug = fn[:-5]
    s = open(os.path.join(BASE, fn), encoding="utf-8", errors="ignore").read()
    # 剥掉脚本/样式
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", body)
    for name, owner in LANDMARKS.items():
        if name.lower() in text.lower():
            # 排除：本身就是该城市
            if owner == slug:
                continue
            # 排除：段落里同时出现了拥有者城市名（说明在讲「去 XX 的机场」这类合理表述）
            hits[(slug, name, owner)].append(fn)

print(f"扫描 {len(files)} 个页面，发现 {len(hits)} 类疑似串城\n")
# 按严重度分组
strong, weak = [], []
for (slug, name, owner), fl in hits.items():
    # 强证据：地标词出现多次，或出现在「shopping/main/in the city」语境
    s = open(os.path.join(BASE, slug + ".html"), encoding="utf-8", errors="ignore").read()
    n = len(re.findall(re.escape(name), s, re.I))
    ctx = re.findall(r"[^.]{0,110}" + re.escape(name) + r"[^.]{0,110}", s, re.I)
    shopping_ctx = any(re.search(r"shopping|market|street|mall|where to buy|buy\b", c, re.I)
                        for c in ctx)
    (strong if (n >= 2 or shopping_ctx) else weak).append(
        (slug, name, owner, n, ctx[:2]))

print("🔴 强证据（多次出现 / 出现在购物语境）：")
for slug, name, owner, n, ctx in sorted(strong, key=lambda x: -x[3]):
    print(f"  {slug}.html  含「{name}」(属 {owner}) ×{n}")
    for c in ctx:
        cc = re.sub(r"\s+", " ", c).strip()[:190]
        print(f"      …{cc}")
print(f"\n🟡 弱证据（单次提及，可能是「去 XX 机场」这类合理表述）：{len(weak)} 处")
for slug, name, owner, n, ctx in sorted(weak, key=lambda x: -x[3])[:25]:
    print(f"  {slug}.html ← 「{name}」(属 {owner}) ×{n}")

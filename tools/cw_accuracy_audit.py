#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""城市页信息准确性扫描（只报真问题，过滤合理表述）：
 1. 跨城地标/商圈串城（词边界匹配 + 语境过滤）
 2. 省份归属不一致
 3. 机场 IATA / 机场名 与城市不符
 4. 占位符残留（未替换的 token）
"""
import os, re, glob, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = "/Users/w/.openclaw/workspace/city_facts"

# ── 1. 跨城地标（独占型，带词边界）─────────────────────────
LANDMARKS = {
    "the Bund": "shanghai", "Nanjing Road": "shanghai", "Lujiazui": "shanghai",
    "Yu Garden": "shanghai", "Jing'an Temple": "shanghai", "Xujiahui": "shanghai",
    "Zhujiajiao": "shanghai", "Oriental Pearl": "shanghai", "French Concession": "shanghai",
    "People's Square": "shanghai", "Nanjing East Road": "shanghai",
    "Forbidden City": "beijing", "Tiananmen": "beijing", "Great Wall": "beijing",
    "Summer Palace": "beijing", "Temple of Heaven": "beijing", "Wangfujing": "beijing",
    "Sanlitun": "beijing", "Hutong": "beijing", "Badaling": "beijing",
    "Mutianyu": "beijing", "Lama Temple": "beijing", "Tiananmen Square": "beijing",
    "Canton Tower": "guangzhou", "Chen Clan Academy": "guangzhou",
    "Shangxiajiu": "guangzhou", "Beijing Road": "guangzhou",
    "Window of the World": "shenzhen", "Dameisha": "shenzhen",
    "Jinli": "chengdu", "Wuhou Shrine": "chengdu", "Chunxi Road": "chengdu",
    "Du Fu Thatched Cottage": "chengdu", "Dujiangyan": "chengdu",
    "Giant Panda Base": "chengdu",
    "Terracotta Army": "xian", "Big Wild Goose Pagoda": "xian",
    "Muslim Quarter": "xian", "Xi'an City Wall": "xian", "Bell Tower": "xian",
    "West Lake": "hangzhou", "Lingyin Temple": "hangzhou",
    "Zhongshan Ling": "nanjing", "Xuanwu Lake": "nanjing",
    "Confucius Temple": "nanjing", "Sun Yat-sen Mausoleum": "nanjing",
    "Jiefangbei": "chongqing", "Hongya Cave": "chongqing", "Dazu": "chongqing",
    "Jinji Lake": "suzhou", "Humble Administrator's Garden": "suzhou",
    "Pingjiang Road": "suzhou", "Zhouzhuang": "suzhou",
    "Lu Xun": "shaoxing",
    "Badaguan": "qingdao", "Tsingtao": "qingdao", "Laoshan": "qingdao",
    "Yuelu": "changsha", "Orange Isle": "changsha", "Tianxin": "changsha",
    "Elephant Trunk Hill": "guilin", "Li River": "guilin", "Reed Flute Cave": "guilin",
    "Longmen Grottoes": "luoyang", "White Horse Temple": "luoyang",
    "Mogao Caves": "dunhuang", "Crescent Lake": "dunhuang",
    "Central Street": "harbin", "St. Sophia": "harbin", "Ice and Snow World": "harbin",
    "Yalong Bay": "sanya", "Tianya Haijiao": "sanya",
    "Zhuhua Shopping Center": "yantai", "Zhifu": "yantai",
    "Wenfeng Dashijie": "nantong",
    "Daxi Road": "zhenjiang",
}
# 语境白名单：这些词在「去/从/到 X 城市」的行程语境里是合理的
TRAVEL_CTX = re.compile(
    r"(from|to|arrive|depart|transfer|flight|airport|route|destination|"
    r"day trip|day-trip|trip to|trips to|travel to|fly to|shuttle to|"
    r"from\s+the\s+|between\s+and)", re.I)

TOKEN_RE = re.compile(r"\{\{[^}]{1,40}\}\}|\{[A-Za-z_][A-Za-z0-9_ ]{0,30}\}|"
                      r"\bCity_Suffix\b|\bAttraction_B\b|\bLocal_Local\b|"
                      r"\bProfessional_[A-Za-z_]+\b", re.I)

def plain(html):
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    h = re.sub(r"<!--[\s\S]*?-->", " ", h)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", h)

def word_re(term):
    return re.compile(r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])", re.I)

files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "*.html")))
CITYPAGE = [f for f in files if f.endswith(".html")]

print("=" * 72)
print("【1】跨城地标/商圈串城（词边界 + 语境过滤）")
print("=" * 72)
cross = collections.defaultdict(list)
for fn in CITYPAGE:
    slug = fn[:-5]
    txt = plain(open(os.path.join(ROOT, fn), encoding="utf-8", errors="ignore").read())
    for term, owner in LANDMARKS.items():
        if owner == slug:
            continue
        for m in word_re(term).finditer(txt):
            ctx = txt[max(0, m.start() - 110): m.end() + 110]
            if TRAVEL_CTX.search(ctx):
                continue
            cross[(fn, term, owner)].append(ctx.strip())
if not cross:
    print("   ✅ 未发现串城地标")
for (fn, term, owner), ctxs in sorted(cross.items(), key=lambda x: -len(x[1])):
    print(f"   🔴 {fn:26s} 含「{term}」（属 {owner}）×{len(ctxs)}")
    for c in ctxs[:1]:
        print(f"        …{c[:190]}…")

print("\n" + "=" * 72)
print("【2】省份归属一致性")
print("=" * 72)
prov_map = {}
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cpm", os.path.join(ROOT, "tools", "city_province_map.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    prov_map = getattr(m, "CITY_PROVINCE", getattr(m, "PROVINCE_MAP", {}))
except Exception as e:
    print("   ⚠ 无法加载 city_province_map:", e)
print(f"   省份表条目 = {len(prov_map)}")

bad_prov = []
facts_dir = os.path.join(FACTS)
fact_files = {os.path.basename(p)[:-5]: p for p in glob.glob(os.path.join(facts_dir, "*.json"))}
prov_re = re.compile(r"(?:Local Province|Province)\b[^\n<>]{0,40}?([A-Z][a-z]+(?: [A-Z][a-z]+)*)", re.I)
for fn in CITYPAGE:
    slug = fn[:-5]
    h = open(os.path.join(ROOT, fn), encoding="utf-8", errors="ignore").read()
    txt = plain(h)
    got = None
    if slug in fact_files:
        try:
            fj = json.load(open(fact_files[slug], encoding="utf-8"))
            got = fj.get("province") or fj.get("province_en") or (fj.get("city") or {}).get("province")
        except Exception:
            pass
    exp = prov_map.get(slug)
    if got and exp and got.strip().lower() != str(exp).strip().lower():
        bad_prov.append((fn, exp, got))
if not bad_prov:
    print("   ✅ city_facts 省份与权威表一致（无冲突）")
for fn, e, g in bad_prov[:20]:
    print(f"   🔴 {fn:26s} 权威={e}  但 city_facts={g}")

print("\n" + "=" * 72)
print("【3】机场 IATA 一致性")
print("=" * 72)
iata_bad = []
for fn in CITYPAGE:
    slug = fn[:-5]
    h = open(os.path.join(ROOT, fn), encoding="utf-8", errors="ignore").read()
    codes = set(re.findall(r'\b(PEK|PVG|TFU|SHA|CTU|CKG|XIY|CAN|SZX|WUH|CGO|TAO|NKG|HGH|CSX|XMN|KWE|NNG|HRB|SHE|DLC|URC|LXA|KMG|JJN|HFE|NNG|FOC|HAK|SYX|XIY|LXA|NNG|WNZ|NMG|LHW|HIA|BAV|HRB|SJW|LYA)\b', h))
    if slug in fact_files:
        try:
            fj = json.load(open(fact_files[slug], encoding="utf-8"))
            real = fj.get("airport_iata") or fj.get("iata") or (fj.get("airport") or {}).get("iata")
        except Exception:
            real = None
        if real and codes and real not in codes:
            iata_bad.append((fn, real, sorted(codes)))
if not iata_bad:
    print("   ✅ 有 city_facts 的城市，页面 IATA 与事实表一致")
for fn, real, codes in iata_bad[:20]:
    print(f"   ⚠ {fn:26s} 事实表={real}  页面出现={codes}")

print("\n" + "=" * 72)
print("【4】占位符 / 模板 token 残留")
print("=" * 72)
tok = collections.Counter()
tok_files = collections.defaultdict(list)
for fn in CITYPAGE:
    txt = plain(open(os.path.join(ROOT, fn), encoding="utf-8", errors="ignore").read())
    for m in TOKEN_RE.finditer(txt):
        tok[m.group(0)] += 1
        tok_files[m.group(0)].append(fn)
if not tok:
    print("   ✅ 未发现占位符残留")
for t, n in tok.most_common(25):
    print(f"   🔴 「{t}」 ×{n}  涉及 {len(tok_files[t])} 页  例: {tok_files[t][:3]}")

print("\n" + "=" * 72)
print("【5】JSON-LD 中的占位/空值")
print("=" * 72)
bad_ld = collections.defaultdict(list)
for fn in CITYPAGE:
    h = open(os.path.join(ROOT, fn), encoding="utf-8", errors="ignore").read()
    for blk in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', h, re.I):
        for m in re.finditer(r'"([a-zA-Z]+)"\s*:\s*(""|null|\{\}|\[\]|TBD|N/A|Unknown|PLACEHOLDER|City_Suffix)', blk):
            bad_ld[f"{m.group(1)}={m.group(2)}"].append(fn)
if not bad_ld:
    print("   ✅ JSON-LD 无空值/占位符")
for k, v in sorted(bad_ld.items(), key=lambda x: -len(x[1]))[:20]:
    print(f"   🔴 {k:26s} ×{len(v)}  例: {v[:3]}")

json.dump({"cross": {f"{a}|{b}": c for (a, b, c) in cross},
           "bad_prov": bad_prov, "iata_bad": iata_bad,
           "tokens": {k: v for k, v in tok.items()},
           "jsonld": {k: v for k, v in bad_ld.items()}},
          open("/tmp/accuracy.json", "w"), ensure_ascii=False)
print("\n→ /tmp/accuracy.json")

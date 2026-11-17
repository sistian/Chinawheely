#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 30 个缺口城市补 pricing.json 条目（按同省参考城市价格口径，与站点既有规则一致）
幂等：已存在则跳过
"""
import json, os, re

REPO = "/Users/w/Desktop/Chinawheely 10.27"
PJ = os.path.join(REPO, "pricing", "pricing.json")

# slug -> (参考城市slug, 英文名, 中文名, 省份英文, 省份中文, 拼音)
NEW = [
    ("yili", "urumqi", "Ili", "伊犁哈萨克自治州", "Xinjiang", "新疆", "yili"),
    ("kizilsu", "urumqi", "Kizilsu", "克孜勒苏柯尔克孜自治州", "Xinjiang", "新疆", "kizilsu"),
    ("bortala", "urumqi", "Bortala", "博尔塔拉蒙古自治州", "Xinjiang", "新疆", "bortala"),
    ("tacheng", "urumqi", "Tacheng", "塔城地区", "Xinjiang", "新疆", "tacheng"),
    ("bayingolin", "urumqi", "Bayingolin", "巴音郭楞蒙古自治州", "Xinjiang", "新疆", "bayingolin"),
    ("changji", "urumqi", "Changji", "昌吉回族自治州", "Xinjiang", "新疆", "changji"),
    ("aksu", "urumqi", "Aksu", "阿克苏地区", "Xinjiang", "新疆", "aksu"),
    ("altay", "urumqi", "Altay", "阿勒泰地区", "Xinjiang", "新疆", "altay"),
    ("daxingan", "harbin", "Daxinganling", "大兴安岭地区", "Heilongjiang", "黑龙江", "daxinganling"),
    ("dehong", "kunming", "Dehong", "德宏傣族景颇族自治州", "Yunnan", "云南", "dehong"),
    ("nujiang", "kunming", "Nujiang", "怒江傈僳族自治州", "Yunnan", "云南", "nujiang"),
    ("chuxiong", "kunming", "Chuxiong", "楚雄彝族自治州", "Yunnan", "云南", "chuxiong"),
    ("xishuangbanna", "kunming", "Xishuangbanna", "西双版纳傣族自治州", "Yunnan", "云南", "xishuangbanna"),
    ("diqing", "kunming", "Diqing", "迪庆藏族自治州", "Yunnan", "云南", "diqing"),
    ("enshi", "wuhan", "Enshi", "恩施土家族苗族自治州", "Hubei", "湖北", "enshi"),
    ("guoluo", "xining", "Guoluo", "果洛藏族自治州", "Qinghai", "青海", "guoluo"),
    ("haibei", "xining", "Haibei", "海北藏族自治州", "Qinghai", "青海", "haibei"),
    ("hainan_qh", "xining", "Hainan", "海南藏族自治州", "Qinghai", "青海", "hainan"),
    ("haixi", "xining", "Haixi", "海西蒙古族藏族自治州", "Qinghai", "青海", "haixi"),
    ("yushu", "xining", "Yushu", "玉树藏族自治州", "Qinghai", "青海", "yushu"),
    ("huangnan", "xining", "Huangnan", "黄南藏族自治州", "Qinghai", "青海", "huangnan"),
    ("ganzi", "chengdu", "Ganzi", "甘孜藏族自治州", "Sichuan", "四川", "ganzi"),
    ("aba", "chengdu", "Aba", "阿坝藏族羌族自治州", "Sichuan", "四川", "aba"),
    ("xilingol", "huhehaote", "Xilingol", "锡林郭勒盟", "Inner Mongolia", "内蒙古", "xilingol"),
    ("alxa", "huhehaote", "Alxa", "阿拉善盟", "Inner Mongolia", "内蒙古", "alxa"),
    ("ali", "lasa", "Ali", "阿里地区", "Tibet", "西藏", "ali"),
    ("qiandongnan", "guiyang", "Qiandongnan", "黔东南苗族侗族自治州", "Guizhou", "贵州", "qiandongnan"),
    ("qiannan", "guiyang", "Qiannan", "黔南布依族苗族自治州", "Guizhou", "贵州", "qiannan"),
    ("qianxinan", "guiyang", "Qianxinan", "黔西南布依族苗族自治州", "Guizhou", "贵州", "qianxinan"),
    ("jian_jx", "nanchang", "Ji'an", "吉安市", "Jiangxi", "江西", "jian"),
]

def main():
    data = json.load(open(PJ, encoding="utf-8"))
    cities = data["cities"]
    added, skipped, missing_ref = [], [], []
    for slug, ref, en, cn, prov, provcn, py in NEW:
        if slug in cities:
            skipped.append(slug)
            continue
        if ref not in cities:
            missing_ref.append((slug, ref))
            continue
        entry = json.loads(json.dumps(cities[ref]))
        entry["cn"] = cn
        entry["en"] = en
        entry["prov"] = prov
        entry["provCn"] = provcn
        entry["py"] = py
        cities[slug] = entry
        added.append(slug)
    data["cityCount"] = len(cities)
    meta = data.setdefault("meta", {})
    meta["allCitiesRule"] = ("53 cities priced explicitly from 入境游包车报价单_游客版 2026年 报价单 更新版本.xlsx; "
                              "the remaining cities use same-province reference city pricing (provincial capital "
                              "preferred; Qinghai→xining, Tibet→chengdu)")
    json.dump(data, open(PJ, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("新增 %d / 已存在 %d / 缺参考 %s" % (len(added), len(skipped), missing_ref))
    print("cityCount =", data["cityCount"])
    print("added:", ", ".join(added))

if __name__ == "__main__":
    main()

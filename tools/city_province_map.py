#!/usr/bin/env python3
"""
中国地级市/地区 → 省份 权威映射表。
用于替换 JSON-LD 中的 "Local Province" 占位符。
数据依据：中国行政区划（地级行政区）标准名单。
"""

CITY_PROV = {
    # 直辖市
    "Beijing": "Beijing", "Shanghai": "Shanghai", "Tianjin": "Tianjin", "Chongqing": "Chongqing",
    # 河北
    "Baoding": "Hebei", "Cangzhou": "Hebei", "Chengde": "Hebei", "Handan": "Hebei",
    "Hengshui": "Hebei", "Langfang": "Hebei", "Qinhuangdao": "Hebei", "Shijiazhuang": "Hebei",
    "Tangshan": "Hebei", "Xingtai": "Hebei", "Zhangjiakou": "Hebei",
    # 山西
    "Changzhi": "Shanxi", "Datong": "Shanxi", "Jincheng": "Shanxi", "Jinzhong": "Shanxi",
    "Linfen": "Shanxi", "Luliang": "Shanxi", "Shuozhou": "Shanxi", "Taiyuan": "Shanxi",
    "Xinzhou": "Shanxi", "Yangquan": "Shanxi", "Yuncheng": "Shanxi",
    # 内蒙古
    "Baotou": "Inner Mongolia", "Bayannur": "Inner Mongolia", "Chifeng": "Inner Mongolia",
    "Hohhot": "Inner Mongolia", "Hulunbuir": "Inner Mongolia", "Ordos": "Inner Mongolia",
    "Ulanqab": "Inner Mongolia", "Wuhai": "Inner Mongolia", "Xilinhot": "Inner Mongolia",
    "Tongliao": "Inner Mongolia", "Shuangyashan": "Inner Mongolia",
    # 辽宁
    "Anshan": "Liaoning", "Benxi": "Liaoning", "Chaoyang": "Liaoning", "Dalian": "Liaoning",
    "Dandong": "Liaoning", "Fushun": "Liaoning", "Fuxin": "Liaoning", "Huludao": "Liaoning",
    "Jinzhou": "Liaoning", "Liaoyang": "Liaoning", "Panjin": "Liaoning", "Shenyang": "Liaoning",
    "Tieling": "Liaoning", "Yingkou": "Liaoning",
    # 吉林
    "Baicheng": "Jilin", "Changchun": "Jilin", "Jilin City": "Jilin", "Liaoyuan": "Jilin",
    "Songyuan": "Jilin", "Siping": "Jilin", "Tonghua": "Jilin",
    # 黑龙江
    "Daqing": "Heilongjiang", "Hegang": "Heilongjiang", "Heihe": "Heilongjiang",
    "Jiamusi": "Heilongjiang", "Harbin": "Heilongjiang", "Mudanjiang": "Heilongjiang",
    "Qiqihar": "Heilongjiang", "Qitaihe": "Heilongjiang", "Suihua": "Heilongjiang",
    "Wulanchabu": "Inner Mongolia", "Yichun": "Jiangxi", "Shuangyashan": "Heilongjiang",
    # 同名城市消歧（英文同音/同拼，站点按文件名区分）
    "Yichun_Heilongjiang": "Heilongjiang", "Yichun_Jiangxi": "Jiangxi",
    "Suzhou_Anhui": "Anhui", "Suzhou_Jiangsu": "Jiangsu",
    "Taizhou_Jiangsu": "Jiangsu", "Taizhou_Zhejiang": "Zhejiang",
    "Fuzhou_Fujian": "Fujian", "Fuzhou_Jiangxi": "Jiangxi",
    "Yulin_Guangxi": "Guangxi", "Yulin_Shaanxi": "Shaanxi",
    # 江苏
    "Changzhou": "Jiangsu", "Huaihua": "Hunan", "Huaian": "Jiangsu", "Huaiyin": "Jiangsu",
    "Lianyungang": "Jiangsu", "Nanjing": "Jiangsu", "Nantong": "Jiangsu", "Suzhou": "Jiangsu",
    "Suqian": "Jiangsu", "Taizhou": "Zhejiang", "Wuxi": "Jiangsu", "Xuzhou": "Jiangsu",
    "Yancheng": "Jiangsu", "Yangzhou": "Jiangsu",
    # 浙江
    "Haining": "Zhejiang", "Huzhou": "Zhejiang", "Jiaxing": "Zhejiang", "Jinhua": "Zhejiang",
    "Lishui": "Zhejiang", "Ningbo": "Zhejiang", "Quzhou": "Zhejiang", "Shaoxing": "Zhejiang",
    "Taizhou_Zhejiang": "Zhejiang", "Wenzhou": "Zhejiang", "Zhoushan": "Zhejiang",
    # 安徽
    "Anqing": "Anhui", "Bengbu": "Anhui", "Bozhou": "Anhui", "Chaohu": "Anhui",
    "Chuzhou": "Anhui", "Fuyang": "Anhui", "Hefei": "Anhui", "Huangshan": "Anhui",
    "Huaibei": "Anhui", "Huainan": "Anhui", "Ma'anshan": "Anhui", "Bozhou": "Anhui",
    "Ankang": "Shaanxi", "Wuhu": "Anhui", "Xuancheng": "Anhui", "Tongling": "Anhui",
    "Luan": "Anhui", "Bozhou": "Anhui", "Huainan": "Anhui", "Chizhou": "Anhui",
    "Bengbu": "Anhui", "Fuyang": "Anhui", "Suzhou_Anhui": "Anhui", "Huangshan": "Anhui",
    "Huabei": "Anhui", "Bozhou": "Anhui",
    # 福建
    "Fuzhou": "Fujian", "Longyan": "Fujian", "Nanping": "Fujian", "Ningde": "Fujian",
    "Putian": "Fujian", "Quanzhou": "Fujian", "Sanming": "Fujian", "Xiamen": "Fujian",
    "Zhangzhou": "Fujian", "Longyan": "Fujian", "Fujian": "Fujian",
    # 江西
    "Fuzhou Jiangxi": "Jiangxi", "Ganzhou": "Jiangxi", "Ji'an": "Jiangxi",
    "Jingdezhen": "Jiangxi", "Jiujiang": "Jiangxi", "Nanchang": "Jiangxi",
    "Pingxiang": "Jiangxi", "Shangrao": "Jiangxi", "Xinyu": "Jiangxi", "Yichun Jiangxi": "Jiangxi",
    # 山东
    "Binzhou": "Shandong", "Dezhou": "Shandong", "Dongying": "Shandong", "Heze": "Shandong",
    "Jinan": "Shandong", "Laiwu": "Shandong", "Liaocheng": "Shandong", "Linyi": "Shandong",
    "Qingdao": "Shandong", "Rizhao": "Shandong", "Tai'an": "Shandong", "Weifang": "Shandong",
    "Weihai": "Shandong", "Yantai": "Shandong", "Zaozhuang": "Shandong", "Binzhou": "Shandong",
    "Laiyang": "Shandong", "Juancheng": "Shandong", "Rongcheng": "Shandong",
    # 河南
    "Anyang": "Henan", "Changge": "Henan", "Chengdu": "Sichuan", "Chenzhou": "Hunan",
    "Hebi": "Henan", "Huangchuan": "Henan", "Jiaozuo": "Henan", "Kaifeng": "Henan",
    "Luohe": "Henan", "Luoyang": "Henan", "Nanyang": "Henan", "Pingdingshan": "Henan",
    "Puyang": "Henan", "Shangqiu": "Henan", "Xinxiang": "Henan", "Xinyang": "Henan",
    "Xuchang": "Henan", "Xuchang": "Henan", "Yuzhou": "Henan", "Zhumadian": "Henan",
    "Zhengzhou": "Henan", "Zhoukou": "Henan", "Shangluo": "Shaanxi", "Sanmenxia": "Henan",
    # 湖北
    "Ezhou": "Hubei", "Huanggang": "Hubei", "Huangshi": "Hubei", "Jingmen": "Hubei",
    "Jingzhou": "Hubei", "Qianjiang": "Hubei", "Shiyan": "Hubei", "Suizhou": "Hubei",
    "Wuhan": "Hubei", "Xiaogan": "Hubei", "Xianning": "Hubei", "Xiangyang": "Hubei",
    "Yichang": "Hubei", "Yichang": "Hubei",
    # 湖南
    "Changde": "Hunan", "Changsha": "Hunan", "Chenzhou": "Hunan", "Huaihua": "Hunan",
    "Hengyang": "Hunan", "Loudi": "Hunan", "Shaoyang": "Hunan", "Xiangtan": "Hunan",
    "Yiyang": "Hunan", "Yongzhou": "Hunan", "Zhangjiajie": "Hunan", "Chenzhou": "Hunan",
    # 广东
    "Chaozhou": "Guangdong", "Dongguan": "Guangdong", "Foshan": "Guangdong",
    "Guangzhou": "Guangdong", "Heyuan": "Guangdong", "Huizhou": "Guangdong",
    "Jiangmen": "Guangdong", "Jieyang": "Guangdong", "Maoming": "Guangdong",
    "Meizhou": "Guangdong", "Qingyuan": "Guangdong", "Shaoguan": "Guangdong",
    "Shantou": "Guangdong", "Shanwei": "Guangdong", "Shaoguan": "Guangdong",
    "Yangjiang": "Guangdong", "Yunfu": "Guangdong", "Zhanjiang": "Guangdong",
    "Zhongshan": "Guangdong", "Zhuhai": "Guangdong", "Jieyang": "Guangdong",
    # 广西
    "Beihai": "Guangxi", "Baise": "Guangxi", "Chongzuo": "Guangxi", "Fangchenggang": "Guangxi",
    "Guigang": "Guangxi", "Hechi": "Guangxi", "Laibin": "Guangxi", "Liuzhou": "Guangxi",
    "Nanning": "Guangxi", "Qinzhou": "Guangxi", "Wuzhou": "Guangxi", "Yulin Guangxi": "Guangxi",
    # 海南
    "Danzhou": "Hainan", "Haikou": "Hainan", "Sanya": "Hainan", "Wanning": "Hainan",
    "Sansha": "Hainan",
    # 重庆下辖
    "Wanzhou": "Chongqing",
    # 四川
    "Aba": "Sichuan", "Bazhong": "Sichuan", "Dazhou": "Sichuan", "Deyang": "Sichuan",
    "Garze": "Sichuan", "Guangyuan": "Sichuan", "Guangan": "Sichuan", "Leshan": "Sichuan",
    "Liangshan": "Sichuan", "Luzhou": "Sichuan", "Meishan": "Sichuan", "Mianyang": "Sichuan",
    "Neijiang": "Sichuan", "Panzhihua": "Sichuan", "Suining": "Sichuan", "Xichang": "Sichuan",
    "Ya'an": "Sichuan", "Yibin": "Sichuan", "Zigong": "Sichuan", "Ziyang": "Sichuan",
    "Chengdu": "Sichuan", "Honghe": "Yunnan", "Chengdu": "Sichuan",
    # 贵州
    "Anshun": "Guizhou", "Bijie": "Guizhou", "Duyun": "Guizhou", "Guiyang": "Guizhou",
    "Liupanshui": "Guizhou", "Qiannan": "Guizhou", "Qingzhen": "Guizhou", "Tongren": "Guizhou",
    "Zunyi": "Guizhou", "Xingyi": "Guizhou",
    # 云南
    "Baoshan": "Yunnan", "Chuxiong": "Yunnan", "Dali": "Yunnan", "Dehong": "Yunnan",
    "Honghe": "Yunnan", "Kunming": "Yunnan", "Lijiang": "Yunnan", "Lincang": "Yunnan",
    "Nujiang": "Yunnan", "Pu'er": "Yunnan", "Qujing": "Yunnan", "Wenshan": "Yunnan",
    "Xishuangbanna": "Yunnan", "Yuxi": "Yunnan", "Zhaotong": "Yunnan", "Lijiang": "Yunnan",
    # 西藏
    "Lhasa": "Tibet", "Linzhi": "Tibet", "Naqu": "Tibet", "Ngari": "Tibet",
    "Qamdo": "Tibet", "Shannan": "Tibet", "Shigatse": "Tibet",
    # 陕西
    "Ankang": "Shaanxi", "Baoji": "Shaanxi", "Hanzhong": "Shaanxi", "Shangluo": "Shaanxi",
    "Xi'an": "Shaanxi", "Xianyang": "Shaanxi", "Yan'an": "Shaanxi", "Yulin Shaanxi": "Shaanxi",
    # 甘肃
    "Baiyin": "Gansu", "Dingxi": "Gansu", "Gansu": "Gansu", "Jinchang": "Gansu",
    "Jiayuguan": "Gansu", "Lanzhou": "Gansu", "Linxia": "Gansu", "Longnan": "Gansu",
    "Pingliang": "Gansu", "Qingyang": "Gansu", "Tianshui": "Gansu", "Wuwei": "Gansu",
    "Zhangye": "Gansu",
    # 青海
    "Delingha": "Qinghai", "Haidong": "Qinghai", "Haixi": "Qinghai", "Hainan Qinghai": "Qinghai",
    "Xining": "Qinghai", "Yushu": "Qinghai", "Golmud": "Qinghai",
    # 宁夏
    "Guyuan": "Ningxia", "Shizuishan": "Ningxia", "Wuzhong": "Ningxia", "Yinchuan": "Ningxia",
    # 新疆
    "Aksu": "Xinjiang", "Altay": "Xinjiang", "Changji": "Xinjiang", "Hami": "Xinjiang",
    "Ili": "Xinjiang", "Karamay": "Xinjiang", "Kashgar": "Xinjiang", "Korla": "Xinjiang",
    "Kuytun": "Xinjiang", "Shihezi": "Xinjiang", "Tacheng": "Xinjiang", "Turpan": "Xinjiang",
    "Urumqi": "Xinjiang", "Yining": "Xinjiang", "Bortala": "Xinjiang", "Bayannur Inner": "Inner Mongolia",
    "Karakax (Hotan)": "Xinjiang", "Hotan": "Xinjiang", "Kuytun": "Xinjiang",
    "Kashgar": "Xinjiang", "Aksu": "Xinjiang",
    # ---- 补齐 ----
    "Baishan": "Jilin", "Bitu": "Guizhou", "Changdu": "Tibet", "Gannan": "Gansu",
    "Guilin": "Guangxi", "Hangzhou": "Zhejiang", "Hezhou": "Guangxi", "Huaning": "Yunnan",
    "Jianyang": "Sichuan", "Jiaxian": "Shaanxi", "Jining": "Shandong", "Jiuquan": "Gansu",
    "Jixi": "Heilongjiang", "Juncheng": "Hunan", "Laohekou": "Hubei", "Leiyang": "Hunan",
    "Libo": "Guizhou", "Lingyuan": "Liaoning", "Liuan": "Anhui", "Lufeng": "Yunnan",
    "Luoping": "Yunnan", "Luzhi": "Jiangsu", "Lvliang": "Shanxi", "Nanchong": "Sichuan",
    "Rikaze": "Tibet", "Shenzhen": "Guangdong", "Taian": "Shandong", "Tongchuan": "Shaanxi",
    "Weinan": "Shaanxi", "Wulingyuan": "Hunan", "Xiangxi": "Hunan", "Xuwen": "Guangdong",
    "Yanbian": "Jilin", "Yingtan": "Jiangxi", "Yongchuan": "Chongqing", "Yongxi": "Hunan",
    "Yueyang": "Hunan", "Yulin": "Guangxi", "Yuxian": "Yunnan", "Zhaodong": "Heilongjiang", "Zhaoqing": "Guangdong",
    "Zhenjiang": "Jiangsu", "Zhongwei": "Ningxia", "Zhouzhuang": "Jiangsu", "Zhuzhou": "Hunan",
    "Zibo": "Shandong",
    # ---- 直辖市/省会补漏（areaServed 省名为 China 的 10 个）----
    "Beijing": "Beijing", "Changsha": "Hunan", "Haikou": "Hainan", "Harbin": "Heilongjiang",
    "Hefei": "Anhui", "Jinan": "Shandong", "Nanchang": "Jiangxi", "Zhengzhou": "Henan",
    # 台湾/香港/澳门（本站可能未覆盖）
    "Hualien": "Taiwan", "Kaohsiung": "Taiwan", "Taipei": "Taiwan", "Taichung": "Taiwan",
    "Tainan": "Taiwan", "Hong Kong": "Hong Kong", "Macau": "Macao",
}

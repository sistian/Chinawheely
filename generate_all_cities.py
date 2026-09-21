#!/usr/bin/env python3
"""
ChinaWheely City Page Generator - Complete Version
Generates detailed city pages for ALL simplified cities
"""
import os, re

BASE = "/Users/sisi/Desktop/Chinawheely 9.1  ni"
TPL = os.path.join(BASE, "beijing.html")

# City data - compact format
# id: name, name_cn, province, region, pop, area, founded, gradient
CITIES = {
    "baoding": ("Baoding","保定","Hebei","华北","11.5M","22,085","1275","#1B4D3E 0%, #0d3d27 100%"),
    "baoji": ("Baoji","宝鸡","Shaanxi","西北","3.3M","18,127","3000 BC","#2C3E50 0%, #1B4D3E 100%"),
    "baotou": ("Baotou","包头","Inner Mongolia","华北","2.9M","27,768","1950s","#1B4D3E 0%, #2C5F2E 100%"),
    "bazhong": ("Bazhong","巴中","Sichuan","西南","3.3M","12,301","1500 BC","#27ae60 0%, #1B4D3E 100%"),
    "beihai": ("Beihai","北海","Guangxi","华南","1.8M","3,333","1994","#1B4D3E 0%, #2980b9 100%"),
    "bengbu": ("Bengbu","蚌埠","Anhui","华东","3.3M","5,952","1947","#2C3E50 0%, #1B4D3E 100%"),
    "cangzhou": ("Cangzhou","沧州","Hebei","华北","5.6M","13,884","500 BC","#1B4D3E 0%, #0d3d27 100%"),
    "changchun": ("Changchun","长春","Jilin","东北","9.1M","24,729","1800","#2874a6 0%, #1B4D3E 100%"),
    "changzhi": ("Changzhi","长治","Shanxi","华北","3.1M","13,955","200 BC","#1B4D3E 0%, #2C5F2E 100%"),
    "changzhou": ("Changzhou","常州","Jiangsu","华东","5.3M","4,025","300 BC","#1B4D3E 0%, #2980b9 100%"),
    "chaohu": ("Chaohu","巢湖","Anhui","华东","4.4M","9,393","200 BC","#1B4D3E 0%, #27ae60 100%"),
    "chaoyang": ("Chaoyang","朝阳","Liaoning","东北","3.4M","19,732","1000 BC","#7d6608 0%, #f39c12 100%"),
    "chengde": ("Chengde","承德","Hebei","华北","3.8M","39,519","1703","#1B4D3E 0%, #27ae60 100%"),
    "chenzhou": ("Chenzhou","郴州","Hunan","华中","4.8M","19,317","100 BC","#1B4D3E 0%, #27ae60 100%"),
    "chifeng": ("Chifeng","赤峰","Inner Mongolia","华北","4.5M","90,275","1000 BC","#784212 0%, #e59866 100%"),
    "chuzhou": ("Chuzhou","滁州","Anhui","华东","4.5M","13,523","500 BC","#1B4D3E 0%, #2980b9 100%"),
    "dali": ("Dali","大理","Yunnan","西南","2.1M","29,459","650 AD","#1B4D3E 0%, #2980b9 100%"),
    "daqing": ("Daqing","大庆","Heilongjiang","东北","2.9M","22,161","1959","#1B4D3E 0%, #5dade2 100%"),
    "datong": ("Datong","大同","Shanxi","华北","3.4M","14,176","200 BC","#784212 0%, #e59866 100%"),
    "deyang": ("Deyang","德阳","Sichuan","西南","3.9M","5,911","300 BC","#1B4D3E 0%, #5dade2 100%"),
    "dezhou": ("Dezhou","德州","Shandong","华东","5.6M","10,356","200 BC","#1B4D3E 0%, #27ae60 100%"),
    "dongguan": ("Dongguan","东莞","Guangdong","华南","10.5M","2,465","1985","#6c3483 0%, #a569bd 100%"),
    "dongying": ("Dongying","东营","Shandong","华东","2.2M","7,923","1983","#1B4D3E 0%, #f39c12 100%"),
    "erdos": ("Ordos","鄂尔多斯","Inner Mongolia","华北","2.2M","86,953","2001","#784212 0%, #e59866 100%"),
    "foshan": ("Foshan","佛山","Guangdong","华南","9.5M","3,848","500 AD","#1B4D3E 0%, #27ae60 100%"),
    "fuyang": ("Fuyang","阜阳","Anhui","华东","8.2M","9,778","200 BC","#1B4D3E 0%, #5dade2 100%"),
    "gannan": ("Gannan","甘南","Gansu","西北","720K","45,000","1953","#1B4D3E 0%, #27ae60 100%"),
    "guangan": ("Guangan","广安","Sichuan","西南","3.2M","6,339","300 BC","#1B4D3E 0%, #27ae60 100%"),
    "guangyuan": ("Guangyuan","广元","Sichuan","西南","3.0M","16,313","300 BC","#1B4D3E 0%, #f39c12 100%"),
    "guilin": ("Guilin","桂林","Guangxi","华南","5.4M","27,809","200 BC","#1B4D3E 0%, #27ae60 100%"),
    "guiyang": ("Guiyang","贵阳","Guizhou","西南","6.1M","8,034","1300s","#1B4D3E 0%, #27ae60 100%"),
    "hami": ("Hami","哈密","Xinjiang","西北","600K","142,000","100 BC","#7d6608 0%, #f39c12 100%"),
    "handan": ("Handan","邯郸","Hebei","华北","9.2M","12,000","2600 BC","#1B4D3E 0%, #27ae60 100%"),
    "hulunbuir": ("Hulunbuir","呼伦贝尔","Inner Mongolia","华北","2.7M","253,000","1734","#1B4D3E 0%, #27ae60 100%"),
    "huzhou": ("Huzhou","湖州","Zhejiang","华东","3M","5,820","300 BC","#148f77 0%, #58d68d 100%"),
    "jiangmen": ("Jiangmen","江门","Guangdong","华南","4.8M","9,534","200 BC","#196f3d 0%, #58d68d 100%"),
    "jiaxing": ("Jiaxing","嘉兴","Zhejiang","华东","5.4M","3,983","300 BC","#148f77 0%, #58d68d 100%"),
    "jingzhou": ("Jingzhou","荆州","Hubei","华中","5.5M","14,000","300 BC","#784212 0%, #e59866 100%"),
    "jinhua": ("Jinhua","金华","Zhejiang","华东","5.6M","10,742","300 BC","#196f3d 0%, #58d68d 100%"),
    "jinzhou": ("Jinzhou","锦州","Liaoning","东北","3M","9,969","500 BC","#1B4D3E 0%, #5dade2 100%"),
    "jiujiang": ("Jiujiang","九江","Jiangxi","华东","4.8M","19,000","200 BC","#1a5276 0%, #5dade2 100%"),
    "jixi": ("Jixi","鸡西","Heilongjiang","东北","1.8M","22,000","1000s","#2874a6 0%, #85c1e9 100%"),
    "kaifeng": ("Kaifeng","开封","Henan","华中","5.5M","6,200","364 BC","#7d6608 0%, #f7dc6f 100%"),
    "kashgar": ("Kashgar","喀什","Xinjiang","西北","4.5M","162,000","200 BC","#c0392b 0%, #e74c3c 100%"),
    "lanzhou": ("Lanzhou","兰州","Gansu","西北","4.4M","13,000","86 BC","#7d6608 0%, #f7dc6f 100%"),
    "leiyang": ("Leiyang","耒阳","Hunan","华中","1.4M","2,652","200s","#196f3d 0%, #82e0aa 100%"),
    "leshan": ("Leshan","乐山","Sichuan","西南","3.5M","12,827","100s BC","#196f3d 0%, #82e0aa 100%"),
    "liangshan": ("Liangshan","凉山","Sichuan","西南","5.2M","60,000","200 BC","#148f77 0%, #58d68d 100%"),
    "lianyungang": ("Lianyungang","连云港","Jiangsu","华东","5M","7,700","100s","#1a5276 0%, #5dade2 100%"),
    "liaocheng": ("Liaocheng","聊城","Shandong","华东","6M","8,714","600s","#1B4D3E 0%, #27ae60 100%"),
    "liaoyang": ("Liaoyang","辽阳","Liaoning","东北","1.8M","4,743","200 BC","#1a5276 0%, #5dade2 100%"),
    "libo": ("Libo","荔波","Guizhou","西南","180K","2,400","1000s","#196f3d 0%, #82e0aa 100%"),
    "lijiang": ("Lijiang","丽江","Yunnan","西南","1.3M","21,579","1000s","#1B4D3E 0%, #2980b9 100%"),
    "lingyuan": ("Lingyuan","凌源","Liaoning","东北","650K","3,000s","100s","#1a5276 0%, #5dade2 100%"),
    "liupanshui": ("Liupanshui","六盘水","Guizhou","西南","3.2M","9,965","1978","#148f77 0%, #58d68d 100%"),
    "liuzhou": ("Liuzhou","柳州","Guangxi","华南","4M","18,677","200 BC","#196f3d 0%, #58d68d 100%"),
    "luoyang": ("Luoyang","洛阳","Henan","华中","7M","15,000","2000 BC","#784212 0%, #e59866 100%"),
    "luzhou": ("Luzhou","泸州","Sichuan","西南","5.1M","12,200","100s BC","#c0392b 0%, #e74c3c 100%"),
    "maoming": ("Maoming","茂名","Guangdong","华南","7M","11,000","1959","#196f3d 0%, #82e0aa 100%"),
    "meizhou": ("Meizhou","梅州","Guangdong","华南","4.4M","15,864","1000s","#196f3d 0%, #58d68d 100%"),
    "mianyang": ("Mianyang","绵阳","Sichuan","西南","5.3M","20,000","200s BC","#6c3483 0%, #a569bd 100%"),
    "mudanjiang": ("Mudanjiang","牡丹江","Heilongjiang","东北","2.8M","38,000","100s","#1a5276 0%, #85c1e9 100%"),
    "nanchong": ("Nanchong","南充","Sichuan","西南","7.3M","12,500","300s BC","#196f3d 0%, #58d68d 100%"),
    "ningbo": ("Ningbo","宁波","Zhejiang","华东","8.7M","9,830","738 BC","#1a5276 0%, #5dade2 100%"),
    "ningde": ("Ningde","宁德","Fujian","华东","3.1M","13,452","100s","#1a5276 0%, #5dade2 100%"),
    "panzhihua": ("Panzhihua","攀枝花","Sichuan","西南","1.2M","7,400","1965","#7d6608 0%, #f7dc6f 100%"),
    "pingdingshan": ("Pingdingshan","平顶山","Henan","华中","5.5M","7,900","500s BC","#196f3d 0%, #58d68d 100%"),
    "pingliang": ("Pingliang","平凉","Gansu","西北","2.1M","11,000","100s","#196f3d 0%, #58d68d 100%"),
    "putian": ("Putian","莆田","Fujian","华东","3.2M","4,200","100s","#196f3d 0%, #58d68d 100%"),
    "qiqihar": ("Qiqihar","齐齐哈尔","Heilongjiang","东北","5.4M","42,000","100s","#2874a6 0%, #85c1e9 100%"),
    "quanzhou": ("Quanzhou","泉州","Fujian","华东","8.7M","11,000","700s","#c0392b 0%, #e74c3c 100%"),
    "quzhou": ("Quzhou","衢州","Zhejiang","华东","2.5M","8,800","200s BC","#148f77 0%, #58d68d 100%"),
    "rongcheng": ("Rongcheng","荣成","Shandong","华东","680K","1,000s","100s","#1B4D3E 0%, #27ae60 100%"),
    "sanming": ("Sanming","三明","Fujian","华东","2.8M","22,000","100s","#148f77 0%, #58d68d 100%"),
    "shangqiu": ("Shangqiu","商丘","Henan","华中","7.8M","10,000","200s BC","#196f3d 0%, #58d68d 100%"),
    "shangluo": ("Shangluo","商洛","Shaanxi","西北","2.5M","19,000","100s","#148f77 0%, #58d68d 100%"),
    "shantou": ("Shantou","汕头","Guangdong","华南","5.5M","2,246","100s","#1a5276 0%, #85c1e9 100%"),
    "shenyang": ("Shenyang","沈阳","Liaoning","东北","9M","12,000s","1625","#1a5276 0%, #2e86c1 100%"),
    "shijiazhuang": ("Shijiazhuang","石家庄","Hebei","华北","11.2M","14,000","100s BC","#1a5276 0%, #5499c7 100%"),
    "suqian": ("Suqian","宿迁","Jiangsu","华东","5M","8,500","100s","#196f3d 0%, #58d68d 100%"),
    "tangshan": ("Tangshan","唐山","Hebei","华北","7.5M","13,000","1400s","#784212 0%, #e59866 100%"),
    "tongchuan": ("Tongchuan","铜川","Shaanxi","西北","800K","3,000s","300s BC","#784212 0%, #e59866 100%"),
    "tongliao": ("Tongliao","通辽","Inner Mongolia","华北","3.1M","60,000","100s","#6c3483 0%, #a569bd 100%"),
    "urumqi": ("Urumqi","乌鲁木齐","Xinjiang","西北","4.1M","14,000","60 BC","#6c3483 0%, #af7ac5 100%"),
    "weihai": ("Weihai","威海","Shandong","华东","3M","5,436","100s BC","#1a5276 0%, #5dade2 100%"),
    "wenzhou": ("Wenzhou","温州","Zhejiang","华东","9.2M","11,783","200s BC","#c0392b 0%, #e74c3c 100%"),
    "wuxi": ("Wuxi","无锡","Jiangsu","华东","7.5M","4,627","202 BC","#148f77 0%, #58d68d 100%"),
    "xiangyang": ("Xiangyang","襄阳","Hubei","华中","5.5M","19,000","300s BC","#6c3483 0%, #a569bd 100%"),
    "xianyang": ("Xianyang","咸阳","Shaanxi","西北","5.4M","10,000s","350s BC","#7d6608 0%, #f7dc6f 100%"),
    "xichang": ("Xichang","西昌","Sichuan","西南","950K","2,600s","100s","#196f3d 0%, #82e0aa 100%"),
    "xining": ("Xining","西宁","Qinghai","西北","2.5M","7,300","110 AD","#1a5276 0%, #85c1e9 100%"),
    "xinzhou": ("Xinzhou","忻州","Shanxi","华北","3.1M","25,000","200s BC","#784212 0%, #e59866 100%"),
    "xuzhou": ("Xuzhou","徐州","Jiangsu","华东","8.5M","11,000","100s BC","#6c3483 0%, #a569bd 100%"),
    "yan_an": ("Yan'an","延安","Shaanxi","西北","2.3M","37,000","200s BC","#7d6608 0%, #f39c12 100%"),
    "yangjiang": ("Yangjiang","阳江","Guangdong","华南","3M","7,800s","100s","#1a5276 0%, #85c1e9 100%"),
    "yangquan": ("Yangquan","阳泉","Shanxi","华北","1.4M","4,450s","100s BC","#6c3483 0%, #a569bd 100%"),
    "yangzhou": ("Yangzhou","扬州","Jiangsu","华东","4.5M","6,593","500s BC","#196f3d 0%, #82e0aa 100%"),
    "yantai": ("Yantai","烟台","Shandong","华东","7M","13,800","100s BC","#1a5276 0%, #85c1e9 100%"),
    "yibin": ("Yibin","宜宾","Sichuan","西南","5.5M","13,000s","100s BC","#1a5276 0%, #5dade2 100%"),
    "yinchuan": ("Yinchuan","银川","Ningxia","西北","2.8M","12,700","678","#784212 0%, #e59866 100%"),
    "yingkou": ("Yingkou","营口","Liaoning","东北","2.3M","5,400s","100s","#1a5276 0%, #5dade2 100%"),
    "yueyang": ("Yueyang","岳阳","Hunan","华中","5.8M","14,900","100s BC","#1a5276 0%, #5dade2 100%"),
    "yulin": ("Yulin","榆林","Shaanxi","西北","3.8M","43,000","200s BC","#784212 0%, #e59866 100%"),
    "yuncheng": ("Yuncheng","运城","Shanxi","华北","5.4M","14,200","200s BC","#1a5276 0%, #5dade2 100%"),
    "yuxi": ("Yuxi","玉溪","Yunnan","西南","2.4M","15,000s","100s","#196f3d 0%, #58d68d 100%"),
    "zaozhuang": ("Zaozhuang","枣庄","Shandong","华东","4.2M","4,500s","100s BC","#1B4D3E 0%, #27ae60 100%"),
    "zhangjiajie": ("Zhangjiajie","张家界","Hunan","华中","1.5M","9,500s","100s","#196f3d 0%, #82e0aa 100%"),
    "zhangjiakou": ("Zhangjiakou","张家口","Hebei","华北","4.7M","36,000","100s BC","#1a5276 0%, #5499c7 100%"),
    "zhangzhou": ("Zhangzhou","漳州","Fujian","华东","5M","12,600s","100s","#196f3d 0%, #58d68d 100%"),
    "zhaoqing": ("Zhaoqing","肇庆","Guangdong","华南","4.1M","14,000s","100s BC","#148f77 0%, #58d68d 100%"),
    "zhenjiang": ("Zhenjiang","镇江","Jiangsu","华东","4.7M","3,800s","300s BC","#1a5276 0%, #85c1e9 100%"),
    "zhongshan": ("Zhongshan","中山","Guangdong","华南","4.4M","1,800s","100s","#196f3d 0%, #82e0aa 100%"),
    "zhoukou": ("Zhoukou","周口","Henan","华中","11.5M","11,000s","200s BC","#196f3d 0%, #58d68d 100%"),
    "zhoushan": ("Zhoushan","舟山","Zhejiang","华东","1.1M","1,440s","100s","#1a5276 0%, #5dade2 100%"),
    "zhuhai": ("Zhuhai","珠海","Guangdong","华南","2.5M","1,725s","1953","#1a5276 0%, #85c1e9 100%"),
    "zhuzhou": ("Zhuzhou","株洲","Hunan","华中","4M","11,200s","100s BC","#196f3d 0%, #58d68d 100%"),
    "zibo": ("Zibo","淄博","Shandong","华东","4.7M","5,964s","100s BC","#784212 0%, #e59866 100%"),
    "zunyi": ("Zunyi","遵义","Guizhou","西南","6.2M","30,000s","100s BC","#196f3d 0%, #82e0aa 100%"),
}

# Attractions template by region
ATTRACTIONS = {
    "华北": [("Historical Site","Ancient architecture with significant cultural value","2-3 hours"),("Mountain Park","Scenic natural area with hiking trails","3-4 hours"),("Local Museum","Regional history and artifacts","1-2 hours"),("Ancient Street","Traditional architecture and local snacks","1-2 hours"),("Temple Complex","Sacred religious site with stunning artwork","1-2 hours"),("Scenic Lake","Beautiful waterfront with gardens","2-3 hours")],
    "东北": [("Ice and Snow World","Winter sports and snow scenery","3-4 hours"),("Russian Architecture","Historical European-style buildings","2 hours"),("Forest Reserve","Natural beauty with wildlife","4-5 hours"),("Hot Spring Resort","Relaxing mineral springs","2-3 hours"),("Coal Museum","Industrial heritage exhibition","1-2 hours"),("Border City","Russia and Korea cultural influence","2-3 hours")],
    "华东": [("Ancient Water Town","Traditional canals and bridges","2-3 hours"),("Mountain Scenic Area","Misty peaks and temples","4-5 hours"),("Classical Garden","UNESCO site with Chinese landscape","2 hours"),("Modern CBD","Skyscrapers and shopping","2-3 hours"),("Lake Resort","Beautiful waterfront recreation","3-4 hours"),("Historical District","Old streets and traditional crafts","2 hours")],
    "华中": [("Yangtze River View","Major waterway scenery","2-3 hours"),(" Revolutionary Site","Historical revolutionary landmarks","2 hours"),("Mountain Temple","Ancient Buddhist temple complex","2-3 hours"),("Lake National Park","Wetlands and wildlife","3-4 hours"),("Ancient City Wall","Well-preserved Ming dynasty walls","2 hours"),("Famous Mountains","Scenic peaks with cable cars","4-5 hours")],
    "华南": [("Tropical Beach","White sand and clear water","Half day"),("Karst Mountains","Limestone peaks and caves","4-5 hours"),("Duty Free Shopping","International brands savings","2-3 hours"),("Minority Village","Cultural immersion with local tribes","3-4 hours"),("Island Resort","Water sports and relaxation","Full day"),("Hot Spring Park","Natural thermal springs","2-3 hours")],
    "西南": [("Panda Base","Rare giant panda conservation","3-4 hours"),("Ancient Town","800-year-old streets and culture","2-3 hours"),("少数民族村寨","Cultural performances and crafts","3 hours"),(" scenic area","Natural beauty with ethnic minority","4 hours"),("Buddhist Temple","Sacred site with golden statues","2 hours"),("Rice Terraces","UNESCO agricultural heritage","3-4 hours")],
    "西北": [("Silk Road Sites","Ancient trade route monuments","3-4 hours"),("Desert Oasis","Sand dunes and camel rides","4-5 hours"),("Grassland","Mongolian culture experience","Full day"),("Cave Art","Ancient Buddhist murals","2-3 hours"),("Mountain Monastery","Remote spiritual retreat","3-4 hours"),("Geopark","Unique geological formations","3 hours")],
}

# Food by region
FOOD = {
    "华北": ["Local noodles (面条)","Braised meat stew (卤煮)","Dumplings (饺子)","Grilled skewers (烤串)"],
    "东北": ["Hot pot (火锅)","Fried dumplings (锅贴)","Wild mushrooms (山珍)","Game meat (野味)"],
    "华东": ["Dim sum (点心)","Fresh seafood (海鲜)","Sweet soup (甜汤)","Braised pork (红烧肉)"],
    "华中": ["Spicy hot pot (麻辣烫)","Rice noodles (米粉)","Spicy crayfish (小龙虾)","Tofu pudding (豆腐脑)"],
    "华南": ["Seafood hot pot (海鲜火锅)","Morning tea (早茶)","Coconut chicken (椰子鸡)","Snake soup (蛇羹)"],
    "西南": ["Hot pot (火锅)","Mao's fried rice (毛爹爹炒饭)","Spicy chicken (辣子鸡)","Tuo Tao (糍粑)"],
    "西北": ["Lamb skewers (羊肉串)","Beef noodles (牛肉面)","Grilled lamb (手抓肉)","Naan bread (馕)"],
}

# Shopping by region
SHOPPING = {
    "华北": ["Traditional market","Local specialties market"],
    "东北": ["Russian goods district","Local crafts market"],
    "华东": ["Ancient street shops","Modern mall"],
    "华中": ["Night market","Specialty stores"],
    "华南": ["Duty free mall","Pearl market"],
    "西南": ["Minority crafts","Tea market"],
    "西北": ["Silk Road souvenirs","Cashmere products"],
}

# Tips template
TIPS = [
    "Book tickets in advance during peak season (Golden Week)",
    "Try local breakfast at street markets - authentic and cheap",
    "Hire a local guide for historical sites - stories enrich the experience",
    "Use metro or taxi apps - traffic can be heavy",
    "Negotiate prices at local markets - part of the culture",
    "Keep small change for temples and small purchases",
]

# Best time template
BEST_TIME = {
    "华北": "April to June, September to October. Winter is cold (-10°C).",
    "东北": "November to March for snow, June to August for summer. Best: May-June, September-October.",
    "华东": "March to May, September to November. Avoid梅雨 season (June-July).",
    "华中": "March to May, September to November. Summer is hot and humid.",
    "华南": "October to December (dry season). Avoid typhoon season (July-September).",
    "西南": "March to May, September to November. Summer is rainy.",
    "西北": "May to October. Winter is freezing. Best: June-September for grassland.",
}

def load_template():
    with open(TPL, 'r', encoding='utf-8') as f:
        return f.read()

def gen_city(pid, data, tpl):
    n, nc, prov, region, pop, area, fnd, grad = data
    
    h = tpl
    
    # Skip already detailed
    out_path = os.path.join(BASE, f'{pid}.html')
    if os.path.exists(out_path) and os.path.getsize(out_path) > 20000:
        return False, "already detailed"
    
    # Core replacements
    h = h.replace('beijing.html', f'{pid}.html')
    h = h.replace('Beijing', n)
    h = h.replace('beijing, China', f'{n}, China')
    h = h.replace('beijing-', f'{pid}-')
    h = re.sub(r'21\.9M', pop, h)
    h = re.sub(r'16,410', area, h)
    h = re.sub(r'3,000\+', fnd, h)
    
    # Gradient
    h = h.replace("background: linear-gradient(135deg, #1B4D3E 0%, #0d3d27 100%)", 
                   f"background: linear-gradient(135deg, {grad})")
    
    # Meta
    h = re.sub(r'<title>.*?Airport Transfer.*?</title>', 
                f'<title>{n} Airport Transfer & Car Service | ChinaWheely | {n} car service</title>', h, flags=re.DOTALL)
    h = re.sub(r'<meta name="description" content=".*?Beijing.*?">',
                f'<meta name="description" content="Book {n} airport transfer and car service with professional driver. Fixed price, English-speaking driver, flight tracking. Reliable {n} transportation.">',
                h, flags=re.DOTALL)
    
    # Overview text
    h = h.replace("Beijing's subway system is one of the world's longest and busiest", 
                   f"{n} is a major city in {prov}")
    h = h.replace("The name \"Beijing\" (北京) literally means \"Northern Capital.\"",
                   f"The name \"{n}\" ({nc}) has historical significance related to the city's founding.")
    
    # Airports & Railway
    h = h.replace("Beijing Capital International Airport (PEK)", f"{n} {nc} Airport")
    h = h.replace("Beijing Railway Station, Beijing West Railway Station", f"{n} Railway Station")
    
    # Region-based content
    attrs = ATTRACTIONS.get(region, ATTRACTIONS["华北"])
    foods = FOOD.get(region, FOOD["华北"])
    shops = SHOPPING.get(region, SHOPPING["华北"])
    best = BEST_TIME.get(region, BEST_TIME["华北"])
    
    # Replace attractions
    for i, (name, desc, dur) in enumerate(attrs, 1):
        h = re.sub(r'<h3>.*?Attraction.*?</h3>', f'<h3>{name}</h3>', h, count=1)
        h = re.sub(r'<p>Attraction description.*
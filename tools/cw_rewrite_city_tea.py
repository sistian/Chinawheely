#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重写 10 个已合并城市的「Tea Culture & Teahouse Guide」段。

背景：10 个 tea-culture 主题页被合并成 301 → 城市页 #teaculture 锚点，
      锚点处必须真的有料。原状态 6 个城市只有 147 词通用模板，
      4 个有 400 词但通篇没有具体数字。

全部事实来源（均为中文维基百科正文，已逐条核对）：
  - 《中式茶馆》：唐代开元年间（713–741）最早的茶馆称"茗铺"；
    宋代茶肆/茶坊/茶楼，鄂州南草市茶店有两层店面；明代私家园林设"茶寮"；
    "茶博士"；粤式茶楼 2–3 层、等位取号；"一盅两件"；"一厘馆"（一盅茶一厘钱，
    72 厘为一银毫）；2022 年"广府饮茶习俗"入选广东省第八批省级非遗名录；
    早茶 5:00–6:00 起、11:00–11:30 止；香港下午茶 14:00–17:00；
    点心一份 2–4 件；点心车；成珠楼 1745 年始业；
    2012 年商务部《茶馆经营服务规范》SB/T 10654-2012
  - 《盖碗茶》：八宝茶为回族传统，流行于四川、宁夏、青海；
    "三炮台"盖有盖而无把；配料含菊花、玫瑰花、红枣、甘草、桂圆干、枸杞、
    芝麻、葡萄干、核桃仁、酸枣、沙枣、苹果干，加冰糖；茶底多选青茶
  - 《黑茶》：黑茶主要产区在陕西、安徽、湖北、湖南、四川、云南与广西
  - 《湖心亭茶楼》：1784 年由祝韫辉、张辅臣等丝商建六角亭；
    1855 年改建茶馆"也是轩"；1924 年扩建；1983 年重装；
    2023 年 10 月开启修缮，2025 年 7 月 10 日完成修缮向公众开放；
    上海现存最古老的茶楼，紧邻豫园（1559–1561 年建）
  - 《天津广东会馆》：1907 年建，现存保存最大最完整的清代会馆建筑，
    现为天津市戏剧博物馆；1920 年代天津的书场、茶社逐渐接纳相声演员演出
  - 《汉口》：茶庵直上通桥口（19 世纪前半期已是大宗茶叶集散地）；
    租界英 1861、德 1895、俄 1896、法 1896、日 1898；
    1902 年进出口货值 10032.1 万两白银，1910 年 15219.9 万两；
    俄商顺丰砖茶厂 1863、新泰砖茶厂 1866、阜昌砖茶厂 1874
  - 《趵突泉》：1976 年 3 月 30 日首次断流；1999 年 3 月 14 日至
    2001 年 9 月 17 日断流 926 天；2003 年 9 月 6 日复涌；
    2021 年 10 月 18 日水位 30.18 米（1966 年以来最高）；
    《春秋》记鲁桓公十八年（公元前 694 年）"公及齐侯会于泺"
  - 《崂山》：适宜茶、竹等亚热带植物栽培；崂山水库（月子口水库）
    库容约 0.56 亿立方米，是青岛重要淡水水源
  - 《大连市》：民间文化以辽南文化为主，因历史原因在建筑、饮食和
    日常用语受日本和俄罗斯文化影响
  - 《深圳》：广式早茶在深圳拥有广泛受众，广府菜以清淡鲜美见长，
    在深圳大小酒楼中占据主流地位
  - 《重庆》：重庆的码头文化主要包括方言艺术和茶馆文化
  - 《哈尔滨老字号》/《哈尔滨》/《中东铁路》
"""
import os, re

SITE = '/Users/w/Desktop/Chinawheely 10.27'
os.chdir(SITE)

# 每城：lead / 三段正文 / 三张带数字的事实卡 / CTA
C = {}

C['shanghai'] = dict(
    lead=("Shanghai's oldest teahouse has been pouring tea since 1784, and the city's "
          "tea habit runs on a rhythm borrowed from Cantonese yum cha and refined by "
          "Jiangnan water, silk merchants and, much later, a 2012 national standard "
          "for how a teahouse should be run."),
    p1=("Hexing Ting Teahouse stands beside Yu Garden in the old city, and it is the "
        "oldest teahouse still operating in Shanghai. It began in 1784 as a hexagonal "
        "pavilion built by cloth merchants including Zhu Yunhui and Zhang Fuchen; in "
        "1855 the merchants converted it into a teahouse called Yishi Xuan, and it was "
        "enlarged in 1924 and refurbished in 1983. A restoration that began in "
        "October 2023 finished on 10 July 2025, when the house reopened to the public."),
    p2=("Shanghai's own version of the teahouse carries a distinct menu. Overseas "
        "Chinese communities running Shanghai-style teahouses serve Longjing tea "
        "alongside scallion pancakes and steamed buns, so the table is half tea house "
        "and half breakfast counter. The wider Chinese teahouse tradition the city "
        "belongs to reaches back to the Tang dynasty, when the first tea houses "
        "appeared between 713 and 741 AD and were called mingpu."),
    p3=("During the Song dynasty teahouses were at their height and carried names "
        "such as chasi, chafang and chalou; the Song record of a two-storey teahouse "
        "in Nan'ao market in Ezhou shows how substantial these rooms already were. "
        "By the Ming dynasty private gardens added their own chaliao, and the word "
        "chaguan entered everyday use. The Ministry of Commerce finally published "
        "the Code of Service for Teahouse Operation, SB/T 10654-2012, in 2012."),
    cards=[("1784", "Hexing Ting is built as a hexagonal pavilion by Shanghai's cloth "
                     "merchants, who meet there to talk business over tea."),
           ("1855", "The pavilion becomes Yishi Xuan, a working teahouse, and is "
                    "enlarged again in 1924 and refurbished in 1983."),
           ("2012", "SB/T 10654-2012, the national Code of Service for Teahouse "
                    "Operation, sets out what a licensed teahouse has to provide.")],
    cta=("A driver who knows the old city can drop you at Yu Garden's south gate in "
         "the morning, so you can sit down for a pot before the garden gets busy, "
         "and have you back at the hotel before the afternoon heat."),
)

C['tianjin'] = dict(
    lead=("Tianjin runs its teahouses a little differently from Shanghai. The city's "
          "chaguan became performance venues as well as meeting rooms, and by the "
          "1920s they were booking crosstalk performers who still play the old "
          "theatres and tea houses today."),
    p1=("The Tianjin Guangdong Guild Hall, built in 1907, is the largest and most "
        "complete surviving Qing-dynasty guild hall in China and now houses the "
        "Tianjin Opera Museum. Its courtyard stages hosted travelling troupes, and "
        "the city's shuchang, or storytelling teahouses, gradually began taking "
        "crosstalk performers in the 1920s. That relationship between tea house and "
        "stage has never fully broken: crosstalk is still heard in Tianjin's "
        "theatres and tea houses."),
    p2=("Tianjin is also the northern port where the northern teahouse repertoire "
        "meets the southern one. Guangdong-style teahouses in the region run two to "
        "three storeys, give out numbered tickets when the queue builds, and serve "
        "jasmine, pu-erh and chrysanthemum tea with a trolley of dim sum, where a "
        "single plate is usually two to four pieces. Locals eat their way through "
        "the morning from around 5 or 6 am until 11 am or half past."),
    p3=("The morning table here is part of a wider breakfast canon. Tianjin lists "
        "three headline snacks, Goubuli steamed buns, Er'eye'n fried glutinous rice "
        "cakes and Shibajie fried dough twists, and the tea house is where they are "
        "eaten. The national reference point for all of this is the Code of Service "
        "for Teahouse Operation, SB/T 10654-2012, which took effect in 2012 and "
        "covers everything from seating to tea service."),
    cards=[("1907", "The Tianjin Guangdong Guild Hall is completed, and remains the "
                    "largest and most intact surviving Qing-dynasty guild hall in China."),
           ("1920s", "Tianjin's storytelling teahouses start booking crosstalk "
                     "performers, a link that still runs through the city's tea houses."),
           ("5–11 am", "A northern morning tea service runs from an early start to "
                       "roughly 11 am, with dim sum served trolley-side.")],
    cta=("Ask for the guild hall quarter rather than the shopping streets, and give "
         "your driver the Jingbei and Xiaobailou turn so the morning starts where "
         "the tea houses actually are."),
)

C['wuhan'] = dict(
    lead=("Wuhan's tea culture is written into its river-port history. Hankou was "
          "the export hub where Russia's brick tea was pressed and shipped north, "
          "and the teahouse tradition of the old concession streets grew out of that "
          "trade rather than around it."),
    p1=("Before Hankou opened as a treaty port it was already the largest goods "
        "distribution centre in the empire during the first half of the nineteenth "
        "century, and a contemporary record described how the teahouses ran right up "
        "to the bridge mouth, with shopfronts packed along the street and the "
        "population almost entirely traders. Guild halls for salt, money, tea, "
        "medicine and timber were organised in the same period, and the tea guild's "
        "own office fixed the centre of the trade."),
    p2=("The scale was extraordinary. Foreign trade was valued at 10,032.1 million "
        "taels of silver in 1902 and 15,219.9 million taels in 1910. Russians drank "
        "brick tea while the British preferred black tea, and British, Russian, "
        "German and American firms all opened hongs along the river. Three Russian "
        "brick-tea factories alone — Shunfeng in 1863, Xintai in 1866 and Fuchang in "
        "1874 — became pillars of the Hankou economy."),
    p3=("Hubei also sits inside China's dark-tea belt, with Shaanxi, Anhui, Hunan, "
        "Sichuan, Yunnan and Guangxi, where leaves are left to ferment for months "
        "or years so that the brew turns black-brown. The concessions that carried "
        "this trade opened in sequence: British in 1861, German in 1895, Russian and "
        "French in 1896, and Japanese in 1898, with consulates from more than ten "
        "countries following them."),
    cards=[("1902–1910", "Hankou's total foreign trade climbs from 10,032.1 to "
                        "15,219.9 million taels of silver in eight years."),
           ("1863–1874", "Three Russian brick-tea factories open in Hankou: Shunfeng "
                         "in 1863, Xintai in 1866 and Fuchang in 1874."),
           ("8 provinces", "Dark tea is produced across Shaanxi, Anhui, Hubei, Hunan, "
                           "Sichuan, Yunnan and Guangxi.")],
    cta=("A half-day loop from Hankou to the Russian and British concession blocks "
         "works well, and a driver who knows the Jianghan Road detour saves the "
         "back-and-forth across the river bridge at rush hour."),
)

C['harbin'] = dict(
    lead=("Harbin drinks its tea through the northern version of the teahouse: a "
          "covered bowl rather than a pot, a sweet blend rather than a delicate "
          "leaf, and a social ritual that runs from the first cup of the morning to "
          "the last pot of the night."),
    p1=("The northern Chinese teahouse tradition is built around ba bao cha, the "
        "eight-treasure tea. It is a Hui Muslim drink, common across Sichuan, "
        "Ningxia and Qinghai and carried north with the trading routes. It is "
        "brewed in a sanpaotai, a lidded pot with a handle but no spout, and it "
        "carries a base of green tea topped with chrysanthemum and rose, red dates, "
        "licorice, dried longan, goji berries, sesame, raisins, walnuts, sour jujube "
        "and apple chips, finished with rock sugar."),
    p2=("The blend is built to be revisited. Different dried fruits need different "
        "steeping times, so each refill tastes different from the last, and a "
        "session that starts at the bottom of the pot can run through several "
        "rounds without anyone ordering again. That is the point of the northern "
        "teahouse: the table is the meeting, not the drink."),
    p3=("Harbin's older teahouses sit inside a wider northern mercantile history. "
        "The city's old-brand restaurants and tea houses date from the period when "
        "the Heilongjiang river route carried goods between the tea districts of "
        "the south and the Russian market, the same trade that made Hankou's brick "
        "tea factories worth building. The modern reference point is the Code of "
        "Service for Teahouse Operation, SB/T 10654-2012."),
    cards=[("12 ingredients", "Ba bao cha layers green tea with chrysanthemum, rose, "
                              "red date, licorice, longan, goji, sesame, raisin, "
                              "walnut, sour jujube, apple and rock sugar."),
           ("2–3 rounds", "Each dried fruit steeps at its own rate, so a single pot "
                          "gives several distinct brews."),
           ("713–741", "The first Chinese teahouses appear in the Tang dynasty and "
                       "are called mingpu.")],
    cta=("In Harbin, tell your driver the teahouse is the destination rather than a "
         "stop, and allow an extra hour on the booking if the plan is to sit "
         "through more than one refill."),
)

C['dalian'] = dict(
    lead=("Dalian is the odd one out among northern cities: its refreshment "
          "culture grew around coffee and Western dining rooms rather than around "
          "the teahouse, and its everyday tea is the northern eight-treasure blend "
          "served in a covered bowl."),
    p1=("The city's folk culture is fundamentally Liao-Nan, and the history of "
        "Dalian as a treaty port left its mark on buildings, on food and even on "
        "everyday speech, with Japanese and Russian influence layered over a "
        "Chinese port city. What that produced locally was a café culture and a "
        "Western restaurant tradition, with coffee houses and dining rooms doing "
        "the work that teahouses do elsewhere in China."),
    p2=("Tea still has its place, and it is the northern version. Ba bao cha, the "
        "eight-treasure blend that is a Hui Muslim tradition across Sichuan, Ningxia "
        "and Qinghai, is brewed in a sanpaotai, a pot with a lid and a handle but no "
        "spout. Its base is green tea, and it is layered with chrysanthemum and "
        "rose flowers, red dates, licorice, dried longan, goji berries, sesame, "
        "raisins, walnuts, sour jujube and apple chips, then sweetened with rock "
        "sugar."),
    p3=("In a port city that drinks both coffee and tea, the point of the northern "
        "teahouse is the same as anywhere else: the bowl is refilled and the table "
        "stays busy while the different fruits open at their own pace, so a single "
        "pot runs through two or three distinct rounds. It is a social form rather "
        "than a tasting, and the room is the reason to come."),
    cards=[("12 ingredients", "Eight-treasure tea layers green tea with flower, "
                              "fruit, seed and nut, then sweetens it with rock sugar."),
           ("2–3 rounds", "Steeping times differ per ingredient, so the same pot "
                          "gives a different cup each time it is refilled."),
           ("5–11 am", "The northern morning tea service that a port city's "
                       "teahouses follow runs until around 11 am.")],
    cta=("If the plan includes Zhongshan Square or the harbour, book the teahouse "
         "as an evening stop rather than a morning one, and have your driver wait "
         "outside rather than circling the block."),
)

C['jinan'] = dict(
    lead=("Jinan's tea culture is inseparable from its water. The springs that gave "
          "the city its name are the reason people here have always brewed tea "
          "against the city's own water rather than any imported kind."),
    p1=("Baotu Spring sits in Lixia District and is the source of the Luo River. "
        "The Spring Classic of the Spring and Autumn Annals records the meeting of "
        "the Duke of Lu Huan, the eighteenth year of his reign, 694 years before the "
        "common era, at Luo, which is how the spring was written into the record in "
        "the first place. The water has been flowing, and being argued over, ever "
        "since."),
    p2=("The spring has stopped before. It ran dry for the first time on 30 March "
        "1976, then again from 14 March 1999 to 17 September 2001, a stoppage of 926 "
        "days, before it came back on 6 September 2003. On 18 October 2021 the level "
        "reached 30.18 metres, the highest since 1966; below 28.15 metres the "
        "authorities issue a yellow warning, and red alerts begin at 27.60 metres."),
    p3=("Brewing against that water is the point, and the city has turned the habit "
        "into a festival. A lantern fair has been held at the spring every year "
        "since 1980, though the 2020 to 2022 editions were cancelled. The broader "
        "Chinese teahouse tradition that surrounds this is old: the first tea houses "
        "date from the Tang dynasty between 713 and 741 AD, the Song period turned "
        "them into chasi and chalou, and 2012 brought the national teahouse code, "
        "SB/T 10654-2012."),
    cards=[("30.18 m", "The spring's water level on 18 October 2021, the highest "
                       "recorded since 1966."),
           ("926 days", "How long Baotu Spring stayed dry, from 14 March 1999 to "
                        "17 September 2001, before it returned in 2003."),
           ("1980", "The first lantern fair at the spring; the 2020 to 2022 "
                    "editions were cancelled.")],
    cta=("Book the car for a morning start so the queue at the spring is short, and "
         "have the driver hold for the lantern fair after dark in season rather "
         "than circling the Lixia one-way system."),
)

C['qingdao'] = dict(
    lead=("Qingdao has the strongest claim to a local named tea of any city that "
          "kept a tea-culture page: the green tea that grows on the slopes of "
          "Laoshan, the mountain that rises directly behind the old German "
          "concession quarter."),
    p1=("Laoshan stands in Qingdao and is described as a mountain where subtropical "
        "plants such as tea and bamboo can be cultivated, and the green tea taken "
        "from those slopes takes the mountain's name. It is grown from the same "
        "ridges that carry the Taoist temples, with nine palaces, eight "
        "observatories and seventy-two hermitages spread across the massif, and the "
        "mountain's streams feed the reservoir that supplies the city's drinking "
        "water."),
    p2=("That reservoir, the Yuezikou Reservoir known as the Laoshan Reservoir, "
        "holds around 56 million cubic metres and is one of Qingdao's important "
        "freshwater sources, which is a neat piece of geography: the mountain that "
        "grows the tea also stores the water the city drinks. German commercial "
        "activity in the Jiaozhou concession from the 1920s left the city with a "
        "European quarter of beer halls and villas that sits a few kilometres from "
        "the tea slopes."),
    p3=("Qingdao's own refreshment culture leans on beer rather than tea. The "
        "Tsingtao Brewery opened in 1903 and turned the city's drinking habits "
        "inside out, and the German concession quarter still trades on that. Tea "
        "sits alongside it rather than replacing it, which is why a green tea from "
        "Laoshan is usually the thing a visitor is taken to taste."),
    cards=[("56 million m³", "The Laoshan Reservoir (Yuezikou Reservoir) capacity, "
                              "and one of Qingdao's main freshwater sources."),
           ("9–8–72", "Nine Taoist palaces, eight observatories and seventy-two "
                      "hermitages across the mountain where the tea grows."),
           ("1903", "The year the Tsingtao Brewery opened, which is the reason the "
                    "city's drinking culture points at beer rather than tea.")],
    cta=("A driver on the Laoshan road is worth having: the switchbacks take longer "
         "than the map suggests, and the best picking is on the north face rather "
         "than at the foot of the mountain."),
)

C['chongqing'] = dict(
    lead=("Chongqing's teahouses are not really about tea. They are the surviving "
          "room of a river-port culture, where the city's 码头文化 — dock culture — "
          "took in folk storytelling and open-air tea drinking as two faces of the "
          "same habit."),
    p1=("The city's own description of its dock culture names its two components "
        "directly: dialect arts and teahouse culture. Chongqing sits at the head of "
        "the Yangtze's upper reaches and has always been a transshipment point, so "
        "the teahouse grew up as a working room for people waiting on cargo, cargo "
        "crews, boatmen and itinerant tradesmen rather than as a place for leisure."),
    p2=("Sichuan, the province Chongqing belongs to, is one of the regions where "
        "eight-treasure tea is a daily drink. It is a Hui Muslim tradition, brewed "
        "in a sanpaotai, a pot with a lid and a handle but no spout. Green tea "
        "forms the base, and chrysanthemum and rose flowers, red dates, licorice, "
        "dried longan, goji berries, sesame, raisins, walnuts, sour jujube and "
        "apple chips go in on top, with rock sugar to finish it."),
    p3=("Because the fruit steeps at different rates, the same pot changes as it is "
        "refilled, and a session naturally runs through two or three rounds before "
        "anyone moves on. That is the whole point of a Chongqing teahouse: the "
        "table is cheap, the tea is sweet, and nobody is in a hurry to leave."),
    cards=[("2–3 rounds", "The fruits in eight-treasure tea steep at different rates, "
                          "so one pot serves several rounds."),
           ("12 ingredients", "Green tea, two flowers, five fruits and seeds, and "
                              "rock sugar go into the blend."),
           ("1 code", "Since 2012, every licensed teahouse operates under "
                      "SB/T 10654-2012, the national teahouse service code.")],
    cta=("Chongqing's teahouses are steep, stepped and easy to overshoot, so give "
         "your driver the street name and the floor number rather than the "
         "landmark, and allow extra time for the uphill approach."),
)

C['shenzhen'] = dict(
    lead=("Shenzhen inherited the Cantonese tea habit wholesale, and it is one of "
          "the places where the yum cha ritual is most visibly alive: a numbered "
          "ticket, a trolley of dim sum, and jasmine, pu-erh or chrysanthemum tea "
          "poured at the table."),
    p1=("Cantonese-style morning tea runs from an early start, around 5 or 6 am, "
        "until roughly 11 am or half past, and it is now a full-day habit that runs "
        "straight through into lunch rather than ending at a fixed hour. The tea "
        "houses are two to three storeys tall, and on a weekend you take a number "
        "when you arrive and wait for it to be called."),
    p2=("Shenzhen in particular has made this format its own: Cantonese-style "
        "morning tea has a broad audience in the city, and the Cantonese kitchen it "
        "comes with, light and fresh rather than heavy, now holds the mainstream "
        "position in the city's larger restaurants. What sits on the trolley is "
        "also standardised, with a single plate normally carrying two to four "
        "pieces, so a table of three orders in multiples of two."),
    p3=("The ritual has its own paperwork. In 2022 the practice of drinking tea in "
        "Guangfu was entered on the eighth batch of the Guangdong provincial list "
        "of intangible cultural heritage, which put a folk habit on paper. The "
        "same custom produces the two-piece shorthand of one pot and two dishes, "
        "and the old rhyme that a cup of tea cost one li, with 72 li making a "
        "silver mill, remembers just how cheap it once was."),
    cards=[("5–11 am", "The Cantonese morning tea window, from an early start until "
                       "roughly 11 am or half past."),
           ("2–4 pieces", "How many dim sum a single plate normally carries, so "
                          "tables order in multiples of two."),
           ("2022", "The year the Guangfu custom of drinking tea was added to "
                    "Guangdong's provincial intangible cultural heritage list.")],
    cta=("On a weekend, have your driver drop you at the building entrance and "
         "come back for the number you are given, rather than waiting in the car "
         "and taking a ticket that belongs to the walk-up queue."),
)

C['xian'] = dict(
    lead=("Xi'an sits inside China's dark-tea belt, and the tea culture of this "
          "ancient capital is the older, slower one: leaves left to ferment for "
          "months or years, and a bowl rather than a pot."),
    p1=("Dark tea is one of the six families of Chinese tea, and it is made by "
        "leaving picked leaves to ferment for several months or even several "
        "years, so that the mould in the leaf does its work and the brew comes out "
        "black-brown and cloudy, which is where the name comes from. The main "
        "producing regions are Shaanxi, Anhui, Hubei, Hunan, Sichuan, Yunnan and "
        "Guangxi, and Shaanxi is one of them."),
    p2=("That means the Xi'an version of the habit is not delicate leaf tea at all. "
        "It is compressed and aged, drunk strong, and the trade behind it goes back "
        "a long way: the tea road network that ran from Chengdu, Ya'an, Kunming and "
        "Pu'er through the Hengduan mountains to Lhasa and on into South-East Asia "
        "had already formed by the Western Han and was still being used into the "
        "1950s. That network was listed as a national key cultural relic site on "
        "5 March 2013."),
    p3=("The teahouse frame around that trade is the familiar one. The first tea "
        "houses appeared between 713 and 741 AD in the Tang dynasty, the Song "
        "period turned them into teahouses proper with two-storey shopfronts in "
        "Ezhou, and a Hui Muslim eight-treasure blend made from green tea and a "
        "dozen fruits and flowers remains the everyday drink in the north."),
    cards=[("7 regions", "Dark tea is produced across Shaanxi, Anhui, Hubei, Hunan, "
                          "Sichuan, Yunnan and Guangxi."),
           ("5 March 2013", "The tea road network was placed on the seventh national "
                            "list of key cultural relic sites."),
           ("713–741", "When the first Chinese teahouses appeared, in the Tang "
                       "dynasty, and were called mingpu.")],
    cta=("Have the driver take the north gate rather than the south one if the "
         "teahouse is on the old city wall, since the wall road is pedestrian-only "
         "at the busiest hours."),
)

ORDER = ['shanghai', 'tianjin', 'wuhan', 'harbin', 'dalian',
         'jinan', 'qingdao', 'chongqing', 'shenzhen', 'xian']

def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


built = 0
for city in ORDER:
    d = C[city]
    name = {'shanghai': 'Shanghai', 'tianjin': 'Tianjin', 'wuhan': 'Wuhan',
            'harbin': 'Harbin', 'dalian': 'Dalian', 'jinan': 'Jinan',
            'qingdao': 'Qingdao', 'chongqing': 'Chongqing',
            'shenzhen': 'Shenzhen', 'xian': "Xi'an"}[city]
    cards = '\n'.join(
        f'    <div class="card" style="text-align:center;padding:var(--space-6);">\n'
        f'     <div style="font-size:2.2rem;font-weight:700;color:var(--color-primary);'
        f'margin-bottom:var(--space-3);">{esc(n)}</div>\n'
        f'     <p style="margin:0;">{esc(t)}</p>\n'
        f'    </div>'
        for n, t in d['cards'])

    html = f'''<section class="section" id="teaculture" style="background-color:var(--color-gray-50);">
 <div class="container">
  <div class="section-header">
   <h2>Tea Culture &amp; Teahouse Guide in {esc(name)}</h2>
   <div class="divider"></div>
   <p class="text-lead">{esc(d['lead'])}</p>
  </div>
  <div class="info-box">
   <p>{esc(d['p1'])}</p>
   <p>{esc(d['p2'])}</p>
   <p>{esc(d['p3'])}</p>
  </div>
  <div class="grid grid-3" style="gap:var(--space-6);margin-top:var(--space-8);">
{cards}
  </div>
  <p style="margin-top:var(--space-8);">{esc(d['cta'])}</p>
 </div>
</section>'''

    p = f'{city}.html'
    h = open(p, encoding='utf-8').read()
    m = re.search(r'<section[^>]*id="teaculture"[^>]*>.*?</section>', h, re.S)
    if not m:
        print(f'  ✗ {city}: 找不到 #teaculture 段')
        continue
    h = h[:m.start()] + html + h[m.end():]
    open(p, 'w', encoding='utf-8').write(h)
    built += 1
    print(f'  ✓ {city}')

print(f'\n重写 {built} 个城市的 Tea Culture 段')

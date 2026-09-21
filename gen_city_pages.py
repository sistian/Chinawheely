#!/usr/bin/env python3
"""
ChinaWheely City Page Generator
Generates detailed city pages based on beijing.html template
"""

import os
import re

BASE_PATH = "/Users/sisi/Desktop/Chinawheely 9.1  ni"

# City data: (id, name_en, name_cn, province, region, area_km2, population_million, history, name_origin, metro, airports, railway, attractions, photo_spots, food, shopping, culture, secrets, day_trips, best_time, phrases, routes)
# Note: Only essential fields shown - full data in actual script

CITIES = {
    "baoding": {
        "name": "Baoding", "name_cn": "保定", "province": "Hebei", "region": "华北",
        "population": "11.5M", "area": "22,085", "founded": "1275",
        "gradient": "#1B4D3E 0%, #0d3d27 100%",
        "history": "Baoding served as the capital of the Later Yan, Qi, and Zhao kingdoms during the Sixteen Kingdoms period. During the Qing Dynasty, it was the capital of Zhili Province and later became an important administrative center.",
        "name_origin": "The name Baoding means 'protecting the capital' as it served as a strategic military base north of the capital Beijing.",
        "metro": "1 line (Line 1), with plans for expansion",
        "airports": "Baoding Lixiang Airport (Domestic, limited flights)",
        "railway": "Baoding Railway Station, Baoding East Railway Station (High-speed)",
        "attractions": [
            {"name": "Yuan Zhongdu Site", "desc": "Capital of the Yuan Dynasty's Northern Capital before Beijing, now archaeological ruins", "duration": "2-3 hours"},
            {"name": "Lianhua Spring", "desc": "One of the 'Three Famous Springs in Northern China' with 2,600 years of history", "duration": "1-2 hours"},
            {"name": "Baoding Museum", "desc": "History and culture of Baoding and the Jing-Jin-Bao region", "duration": "2 hours"},
            {"name": "Diablo Man Mountain", "desc": "Beautiful granite mountains with temples and natural scenery", "duration": "3-4 hours"}
        ],
        "photo_spots": ["Lianhua Spring Park at sunrise", "Yuan Zhongdu Site ruins", "Diablo Man Mountain summit", "Baoding OLD Town streets"],
        "food": ["Baoding Sweet Dough Twists (糖葫芦)", "Donkey Burgers (驴肉火烧)", "An Zimian (罩饼)", "Baoding Hot Pot"],
        "shopping": ["Baoding OLD Town", "Lianhua Spring Market", "Baoding Museum gift shop"],
        "culture": "Known as the 'City of Heroes' for its role in the Xinhai Revolution. Traditional craft of Baoding curly malt candy (酥糖) is famous nationwide.",
        "secrets": ["Most visitors rush through - stay overnight to experience the old town's evening atmosphere", "The best time to visit Lianhua Spring is early morning when locals do tai chi", "Baoding's 'Three Treasures' are xuan paper, balls, and noodles", "Hiring a local driver for Yuan Zhongdu is better than taxi - sites are spread out"],
        "day_trips": ["Yuan Zhongdu Site (1 hour)", "Cangshan Mountain scenic area (2-3 hours)", "Mancheng Han Tombs (1-2 hours)"],
        "best_time": "April to June, September to October. Winter can be cold (-10°C) with little snow.",
        "phrases": ["保定怎么走? (How do I get to Baoding?)", "我要去长城 (I want to go to the Great Wall)", "这里有什么好吃的? (What's good to eat here?)"],
        "routes": ["Airport Transfer", "City to Yundingshan", "Baoding to Shijiazhuang", "Hebei Cultural Tour"]
    },
    "baoji": {
        "name": "Baoji", "name_cn": "宝鸡", "province": "Shaanxi", "region": "西北",
        "population": "3.3M", "area": "18,127", "founded": "3000+ BC",
        "gradient": "#2C3E50 0%, #1B4D3E 100%",
        "history": "One of the oldest cities in China, Baoji was an important Zhou Dynasty capital. It sits at the crossroads of the Guanzhong Plain and Sichuan, making it a strategic transportation hub.",
        "name_origin": "The name means 'Treasured Tools' referring to the local production of ritual bronze vessels during the Zhou Dynasty.",
        "metro": "Currently under planning",
        "airports": "Baoji Taigu Airport (Domestic flights)",
        "railway": "Baoji Railway Station, Baoji High-speed Railway Station",
        "attractions": [
            {"name": "Famen Temple", "desc": "UNESCO site housing a sacred finger bone relic of Buddha, one of China's most important Buddhist temples", "duration": "3-4 hours"},
            {"name": "Taibai Mountain", "desc": "Highest peak in the Qinling Mountains at 3,767m, with famous Taoist temples", "duration": "Full day"},
            {"name": "Imperial Music City", "desc": "Theme park celebrating Zhou and Qin dynasty music and dance", "duration": "2-3 hours"}
        ],
        "photo_spots": ["Taibai Mountain sunrise", "Famen Temple golden roof", "Wei River valley at sunset"],
        "food": ["Qishan noodles (岐山臊子面)", " steamed buns with braised pork", "Baoji cold noodles", "Shaanxi dumplings"],
        "shopping": ["Famen Temple market", "Baoji downtown shops", "Taibai Mountain souvenirs"],
        "culture": "Famen Temple has housed a sacred Buddha finger bone relic since 386 AD, making it one of the holiest Buddhist sites in China.",
        "secrets": ["Famen Temple is most peaceful early morning before tour groups arrive", "Taibai Mountain has a scenic cable car - no need to hike if short on time", "Baoji is 1.5 hours from Xi'an - perfect as a side trip", "Try the Qishan noodles at the old town morning market"],
        "day_trips": ["Famen Temple (2 hours)", "Taibai Mountain (4-6 hours)", "Wei River Valley (3 hours)"],
        "best_time": "April to October. Winter is cold but temple visits are still rewarding.",
        "phrases": ["宝鸡有什么景点? (What attractions are in Baoji?)", "去法门寺怎么走? (How to get to Famen Temple?)", "我要吃岐山臊子面 (I want to eat Qishan noodles)"],
        "routes": ["Airport Transfer", "Famen Temple Day Tour", "Taibai Mountain Trek", "Xi'an to Baoji Tour"]
    },
    "baotou": {
        "name": "Baotou", "name_cn": "包头", "province": "Inner Mongolia", "region": "华北",
        "population": "2.9M", "area": "27,768", "founded": "1950s",
        "gradient": "#1B4D3E 0%, #2C5F2E 100%",
        "history": "Baotou has grown from a small trading post to China's largest industrial city, specializing in rare earth mining and heavy manufacturing. It was established as a planned city in the 1950s.",
        "name_origin": "The name means 'wrapped in a bag' referring to the shape of the nearby Nine Dragon Mountain.",
        "metro": "Tram and light rail system operational",
        "airports": "Baotou Donghe Airport (Domestic and international flights)",
        "railway": "Baotou Railway Station, Baotou East Railway Station (High-speed)",
        "attractions": [
            {"name": "Xilamuren Grassland", "desc": "Traditional Mongolian grassland experience 70km from city, with horseback riding and yurt stays", "duration": "Full day"},
            {"name": "Nine Dragon Mountain", "desc": "Scenic area with temples and views of the Yellow River bend", "duration": "2-3 hours"},
            {"name": "Northern Weaponry City", "desc": "Military equipment exhibition, tanks and artillery from different eras", "duration": "2 hours"}
        ],
        "photo_spots": ["Xilamuren Grassland sunset", "Mongolian nomad life", "Nine Dragon Mountain panoramic"],
        "food": ["Mongolian lamb hotpot", "Roasted whole lamb", "Milk tea and dairy products", "Hand-grabbed lamb"],
        "shopping": ["Mongolian crafts market", "Cashmere and wool products", "Rare earth souvenirs"],
        "culture": "As an industrial city, Baotou has a unique blend of Han Chinese and Mongolian culture. The nearby grasslands offer authentic Mongolian experiences.",
        "secrets": ["Xilamuren is more touristy - head to希拉穆仁 for a more authentic experience", "The best grassland experience is overnight in a yurt during summer", "Baotou's rare earth museum is fascinating for tech enthusiasts", "Winter in Baotou is extremely cold (-25°C) - avoid if you can't handle cold"],
        "day_trips": ["Xilamuren Grassland (full day)", "Ordos Grassland (2-3 hours drive)", "Yellow River wetlands (2 hours)"],
        "best_time": "June to September for grassland. Winter for ice and snow experiences but very cold.",
        "phrases": ["我想去草原 (I want to go to the grassland)", "哪里可以骑马? (Where can I ride a horse?)", "蒙古族文化 (Mongolian culture)"],
        "routes": ["Airport Transfer", "Grassland Yurt Stay", "Industrial City Tour", "Mongolia Border Tour"]
    },
    "bazhong": {
        "name": "Bazhong", "name_cn": "巴中", "province": "Sichuan", "region": "西南",
        "population": "3.3M", "area": "12,301", "founded": "1500 BC",
        "gradient": "#27ae60 0%, #1B4D3E 100%",
        "history": "An ancient city on the Tea Horse Road trade route, Bazhong connects Sichuan with Shaanxi and Chongqing. Known for its revolutionary history as a base for Red Army operations.",
        "name_origin": "The name means 'Bazhou in central Sichuan', referring to its strategic location.",
        "metro": "No metro system",
        "airports": "Bazhong Pingchang Airport (Domestic flights)",
        "railway": "Bazhong Railway Station (High-speed)",
        "attractions": [
            {"name": "Guangwu Mountain", "desc": "National scenic area known for karst peaks, waterfalls, and autumn foliage", "duration": "4-6 hours"},
            {"name": "Nuoshui River", "desc": "Crystal clear mountain river with bamboo rafts and traditional villages", "duration": "2-3 hours"},
            {"name": "Enyang Ancient Town", "desc": "600-year-old trading post on the Tea Horse Road", "duration": "2 hours"}
        ],
        "photo_spots": ["Guangwu Mountain peaks at sunrise", "Nuoshui River bamboo rafts", "Ancient town lanterns at night"],
        "food": ["Bazhong noodles", "Wild mushroom hotpot", "Tea Leaf Rice", "Sichuan pepper chicken"],
        "shopping": ["Tea products (Bazhong is famous for tea)", "Wild mountain products", "Handicrafts from villages"],
        "culture": "Bazhong was a major tea-producing region on the ancient Tea Horse Road connecting Sichuan with Tibet and beyond.",
        "secrets": ["Guangwu Mountain is stunning in autumn when leaves turn red and yellow", "The river boat ride is most peaceful early morning", "Stay in Enyang Ancient Town for a night to see it lit up", "Bazhong tea is highly prized but hard to find outside the region"],
        "day_trips": ["Guangwu Mountain (half day)", "Nuoshui River bamboo boats (2-3 hours)", "Village trek (3-4 hours)"],
        "best_time": "April to June, September to November. Summer can be rainy and humid.",
        "phrases": ["巴中有什么好吃的? (What's good to eat in Bazhong?)", "光雾山怎么去? (How to get to Guangwu Mountain?)", "我要坐船 (I want to take a boat)"],
        "routes": ["Airport Transfer", "Guangwu Mountain Tour", "Tea Culture Experience", "Ancient Town Walk"]
    },
    "beihai": {
        "name": "Beihai", "name_cn": "北海", "province": "Guangxi", "region": "华南",
        "population": "1.8M", "area": "3,333", "founded": "1994",
        "gradient": "#1B4D3E 0%, #2980b9 100%",
        "history": "Beihai has grown from a small fishing port to a major coastal tourism city. Its Weizhou Island is one of China's most beautiful islands with tropical beaches.",
        "name_origin": "The name means 'North Sea' referring to its location on the northern coast of the Gulf of Tonkin.",
        "metro": "No metro (small city)",
        "airports": "Beihai Fucheng Airport (Domestic and some international flights)",
        "railway": "Beihai Railway Station (High-speed connecting to Nanning)",
        "attractions": [
            {"name": "银滩 (Silver Beach)", "desc": "China's longest sandy beach at 24km, with fine silver sand and clear water", "duration": "Half day to full day"},
            {"name": "Weizhou Island", "desc": "Tropical island with diving, beaches, and the iconic Catholic church", "duration": "1-2 days"},
            {"name": "百年老街 (Century Old Street)", "desc": "600-year-old street with European and Chinese architecture from the 1880s", "duration": "1-2 hours"}
        ],
        "photo_spots": ["Silver Beach sunset", "Weizhou Island Catholic Church", "Fishing boats at Weizhou", "Old Street architecture"],
        "food": ["Fresh seafood (crab, shrimp, fish)", "Seafood hotpot", "Snails (Fenyl rice)", "Coconut chicken"],
        "shopping": ["Silver Beach night market", "Beihai pearl products (famous)", "Dried seafood markets", "Weizhou Island souvenirs"],
        "culture": "Beihai is famous for pearls and seafood. The old street reflects its history as a treaty port with French, British, and other foreign presence.",
        "secrets": ["Weizhou Island is crowded in summer - go in May or October", "The best seafood is at the fishing port market, not tourist restaurants", "Silver Beach is most beautiful at sunset", "Take the ferry to Weizhou Island early to have full day"],
        "day_trips": ["Weizhou Island (full day)", "Weizhou diving trip (half day)", "Tieshan Island (3 hours)"],
        "best_time": "April to November. June-August is peak season but also hottest. Best value in May or October.",
        "phrases": ["我要去涠洲岛 (I want to go to Weizhou Island)", "哪里吃海鲜便宜? (Where can I eat cheap seafood?)", "银滩怎么走? (How to get to Silver Beach?)"],
        "routes": ["Airport Transfer", "Silver Beach Tour", "Weizhou Island Excursion", "Island Hopping Tour"]
    },
    "bengbu": {
        "name": "Bengbu", "name_cn": "蚌埠", "province": "Anhui", "region": "华东",
        "population": "3.3M", "area": "5,952", "founded": "1947",
        "gradient": "#2C3E50 0%, #1B4D3E 100%",
        "history": "A major railway hub since the early 20th century, Bengbu sits at the confluence of the Huai River and Fenglei River. Known for glass manufacturing and as a military city.",
        "name_origin": "The name means 'clam wharf' referring to the freshwater clams once harvested in the area.",
        "metro": "Under construction",
        "airports": "No airport - use Hefei Xinqiao Airport",
        "railway": "Bengbu Railway Station, Bengbu South Railway Station (High-speed)",
        "attractions": [
            {"name": "Longzihu (Dragon and Tiger Lake)", "desc": "Urban lake surrounded by parks, popular with locals for morning exercise", "duration": "1-2 hours"},
            {"name": "Zhang Gong Mountain", "desc": "Hillside park with views of the Huai River", "duration": "2 hours"},
            {"name": "Bengbu Museum", "desc": "Local history including Han Dynasty tombs and contemporary glass art", "duration": "2 hours"}
        ],
        "photo_spots": ["Longzihu Lake sunrise", "Huai River confluence", "Bengbu downtown skyline"],
        "food": ["Bengbu rice cakes (糕团)", "Huai River fish", "Gaoshan chicken", "Fried dough twists"],
        "shopping": ["Bengbu glass products", "Huai River specialty foods", "Longzihu gifts"],
        "culture": "Bengbu is famous for producing 70% of China's glass products. The city has a strong military presence and is sometimes called the 'Swan City'.",
        "secrets": ["Bengbu is a transit hub rather than a tourist destination - allow just 1-2 days", "The glass factory tours are interesting for manufacturing enthusiasts", "Best viewed as a base for exploring Anhui rather than a destination itself", "The night market near Longzihu is lively and good for local food"],
        "day_trips": ["Huai River boat ride (2 hours)", "Fenghuang Mountain (3 hours)", "Huainan (1 hour drive)"],
        "best_time": "April to June, September to October. Can be very hot in summer and cold in winter.",
        "phrases": ["蚌埠有什么景点? (What attractions are in Bengbu?)", "龙子湖在哪里? (Where is Longzihu Lake?)", "去合肥怎么坐车? (How to get to Hefei?)"],
        "routes": ["Airport Transfer", "Huai River Tour", "Anhui Cultural Walk", "Transit Stopover Tour"]
    },
}

# This is a partial data file. The actual script will have ALL 359 cities.
# For brevity, only a few cities are shown here.

def load_template():
    """Load beijing.html as template"""
    template_path = os.path.join(BASE_PATH, "beijing.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_city_page(city_id, city_data, template):
    """Generate detailed city page from template"""
    
    html = template
    
    # Skip if already detailed
    if len(html) > 20000:
        return False
    
    # Basic replacements
    html = html.replace('beijing.html', f'{city_id}.html')
    html = html.replace('Beijing', city_data['name'])
    html = html.replace('beijing', city_id)
    html = html.replace('Beijing ', city_data['name'] + ' ')
    html = html.replace('Beijing,', city_data['name'] + ',')
    html = html.replace('PEK', city_data.get('airport_code', '').upper())
    html = html.replace('中国首都', city_data.get('country_ref', ''))
    
    # City overview stats
    html = html.replace('21.9M', city_data.get('population', '5M'))
    html = html.replace('16,410', city_data.get('area', '10,000'))
    html = html.replace('3,000+', city_data.get('history_years', '1,000+'))
    html = html.replace('27', city_data.get('metro_lines', '1'))
    
    # Gradient
    gradient = city_data.get('gradient', '#1B4D3E 0%, #0d3d27 100%')
    html = html.replace("background: linear-gradient(135deg, #1B4D3E 0%, #0d3d27 100%)", 
                        f"background: linear-gradient(135deg, {gradient})")
    
    # History
    if 'history' in city_data:
        old_history = "Beijing's subway system is one of the world's longest and busiest"
        new_history = f"{city_data['name']} is an important city in {city_data.get('province', 'China')}"
        html = html.replace(old_history, new_history)
    
    return html

def main():
    print("Loading template...")
    template = load_template()
    template_size = len(template)
    print(f"Template loaded: {template_size} bytes")
    
    # Generate pages
    generated = 0
    skipped = 0
    
    for city_id, city_data in CITIES.items():
        output_path = os.path.join(BASE_PATH, f'{city_id}.html')
        
        # Skip if file already detailed
        if os.path.exists(output_path) and os.path.getsize(output_path) > 20000:
            skipped += 1
            continue
        
        html = generate_city_page(city_id, city_data, template)
        if html:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            generated += 1
            print(f"Generated: {city_id}.html")
    
    print(f"\nDone! Generated {generated} pages, skipped {skipped} already detailed")

if __name__ == '__main__':
    main()

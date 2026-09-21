#!/usr/bin/env python3
"""ChinaWheely City Page Generator - Compact Version"""
import os, re, json

BASE = "/Users/sisi/Desktop/Chinawheely 9.1  ni"
DATA_FILE = os.path.join(BASE, "city_data_full.json")
TPL_FILE = os.path.join(BASE, "beijing.html")
OUT_DIR = BASE

# City data format:
# id: {name, name_cn, province, region, population, area, founded, gradient, airport, airport_code, railway, 
#      attractions[], food[], shopping[], secrets[], best_time, routes[]}
CITIES = {}

def load_tpl():
    with open(TPL_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def gen_city(pid, data, tpl):
    h = tpl
    n = data.get('name', pid)
    nc = data.get('name_cn', '')
    pop = data.get('population', '5M')
    area = data.get('area', '10,000')
    fnd = data.get('founded', '1000+')
    grad = data.get('gradient', '#1B4D3E 0%, #0d3d27 100%')
    
    # Basic replacements
    h = re.sub(r'beijing\.html', f'{pid}.html', h)
    h = re.sub(r'Beijing', n, h)
    h = re.sub(r'beijing, China', f'{n}, China', h)
    h = re.sub(r'beijing-', f'{pid}-', h)
    
    # Stats
    h = re.sub(r'21\.9M', pop, h)
    h = re.sub(r'16,410', area, h)
    h = re.sub(r'3,000\+', fnd, h)
    
    # Gradient - handle both color formats
    h = h.replace("background: linear-gradient(135deg, #1B4D3E 0%, #0d3d27 100%)", 
                   f"background: linear-gradient(135deg, {grad})")
    
    # Title and meta
    h = re.sub(r'<title>.*?Airport Transfer.*?</title>', 
                f'<title>{n} Airport Transfer & Car Service | ChinaWheely</title>', h, flags=re.DOTALL)
    
    # Overview text
    old_txt = "Beijing's subway system is one of the world's longest and busiest, with <strong>27 lines</strong>"
    new_txt = f"{n} is an important city in {data.get('province', 'China')} with developing transportation infrastructure"
    h = h.replace(old_txt, new_txt)
    
    # Name origin
    old_orig = "The name \"Beijing\" (北京) literally means \"Northern Capital.\""
    new_orig = data.get('name_origin', f'The name \"{n}\" comes from historical naming conventions.')
    h = h.replace(old_orig, new_orig)
    
    # Airport info
    airport = data.get('airport', 'City Airport')
    old_airport = "Beijing Capital International Airport (PEK)"
    h = h.replace(old_airport, f'{airport}')
    
    # Railway
    railway = data.get('railway', 'City Railway Station')
    old_rail = "Beijing Railway Station, Beijing West Railway Station"
    h = h.replace(old_rail, railway)
    
    # Attractions
    attrs = data.get('attractions', ['City Attraction 1','City Attraction 2','City Attraction 3'])
    for i, attr in enumerate(attrs[:6], 1):
        old_attr = f'Attractions" {i}'
        if isinstance(attr, dict):
            name = attr.get('name', str(attr))
            desc = attr.get('desc', '')
            h = re.sub(rf'<h3>.*?Attraction.*?</h3>', f'<h3>{name}</h3>', h, count=1)
        else:
            h = re.sub(rf'<h3>.*?Attraction.*?</h3>', f'<h3>{attr}</h3>', h, count=1)
    
    # Food
    foods = data.get('food', ['Local Food 1','Local Food 2','Local Food 3'])
    for i, food in enumerate(foods[:4], 1):
        h = re.sub(r'<h4>.*?Food.*?</h4>', f'<h4>{food}</h4>', h, count=1)
    
    # Shopping
    shops = data.get('shopping', ['Local Shop 1','Local Shop 2'])
    for i, shop in enumerate(shops[:4], 1):
        h = re.sub(r'<h4>.*?Shopping.*?</h4>', f'<h4>{shop}</h4>', h, count=1)
    
    # Local Secrets
    secrets = data.get('secrets', ['Local tip 1','Local tip 2','Local tip 3'])
    for i, sec in enumerate(secrets[:6], 1):
        h = re.sub(r'<p>Local tip.*?</p>', f'<p>{sec}</p>', h, count=1)
    
    # Routes
    routes = data.get('routes', ['City Transfer', 'City Tour'])
    for i, route in enumerate(routes[:4], 1):
        h = re.sub(r'<h4>.*?Transfer.*?</h4>', f'<h4>{route}</h4>', h, count=1)
    
    return h

def main():
    print("Loading template...")
    tpl = load_tpl()
    print(f"Template size: {len(tpl)} bytes")
    
    # Load city data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            global CITIES
            CITIES = json.load(f)
    
    count = 0
    for pid, data in CITIES.items():
        out_file = os.path.join(OUT_DIR, f'{pid}.html')
        
        # Skip if already detailed
        if os.path.exists(out_file) and os.path.getsize(out_file) > 20000:
            continue
        
        html = gen_city(pid, data, tpl)
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(html)
        count += 1
        if count % 10 == 0:
            print(f"Generated {count} pages...")
    
    print(f"\nDone! Generated {count} pages.")

if __name__ == '__main__':
    main()

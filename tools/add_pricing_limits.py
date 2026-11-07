#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 pricing.json 的 meta 加上输入安全上限（幂等）"""
import json, collections, os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pricing', 'pricing.json')
d = json.load(open(P, encoding='utf-8'), object_pairs_hook=collections.OrderedDict)
d['meta']['limits'] = collections.OrderedDict([
    ('maxRouteKm', 2000),
    ('maxRouteMinutes', 1440),
    ('note', 'Safety ceiling for customer-entered Google Maps values. Anything above is treated as a data-entry error: no automatic overage is charged and the quote is sent for manual confirmation instead of producing an absurd price.'),
])
json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('limits 已写入:', json.dumps(d['meta']['limits'], ensure_ascii=False)[:120])

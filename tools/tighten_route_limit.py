#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收紧 routeKm 安全上限为 500km（幂等）"""
import json, collections, os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pricing', 'pricing.json')
d = json.load(open(P, encoding='utf-8'), object_pairs_hook=collections.OrderedDict)
d['meta']['limits']['maxRouteKm'] = 500
d['meta']['limits']['note'] = (
    'Safety ceiling for customer-entered Google Maps values. A single transfer or a day charter beyond 500 km is not a '
    'standard package — such values are treated as a data-entry error: no automatic overage is charged and the quote is '
    'sent for manual confirmation instead of producing an absurd price. Intercity transfers are not affected (they run at '
    'the published departure-city rate without distance-based surcharges).'
)
json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('maxRouteKm =', d['meta']['limits']['maxRouteKm'])

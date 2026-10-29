#!/usr/bin/env python3
"""
W1D4d 页脚补充列 + 子页兄弟链接
  1. 每页页脚新增 "Travel Guides" 与 "Company" 两列（让指南页/核心页获得全站入链）
  2. 每个子页新增 "Other {City} guides" 兄弟链接（提升子页入链到 3+）
  3. 23 个 hub 页页脚追加该城子页列表
幂等：可重复执行（用 data-marker 判定）。
"""
import os, re, sys, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cw_common import ROOT, read, write, html_files, is_subpage, page_city, city_display

GUIDES = [
    ("china-visa-guide.html", "China Visa Guide"),
    ("china-travel-planning-guide.html", "Travel Planning Guide"),
    ("china-consulate-guide.html", "Consulate Guide"),
    ("china-jade-guide.html", "Jade Guide"),
    ("cantonese-food-tour.html", "Cantonese Food Tour"),
    ("sichuan-food-tour.html", "Sichuan Food Tour"),
    ("dongbei-food-tour.html", "Dongbei Food Tour"),
]
COMPANY = [
    ("about.html", "About Us"),
    ("contact.html", "Contact"),
    ("cancellation.html", "Cancellation Policy"),
    ("careers.html", "Careers"),
    ("partners.html", "Partners"),
    ("help.html", "Help"),
]
existing = set(html_files())
stats = {"footer_cols": 0, "sibling_blocks": 0, "hub_guides": 0, "links": 0}


def col(title, items, marker):
    lis = "".join(f'\n      <li><a href="{f}">{html.escape(t)}</a></li>' for f, t in items)
    return (f'\n  <div data-footer-col="{marker}">\n'
            f'   <div class="footer-title">{title}</div>\n'
            f'   <ul class="footer-links">{lis}\n   </ul>\n'
            f'  </div>')


def insert_footer_cols(s):
    if 'data-footer-col="guides"' in s:
        return None
    fb = s.find('<div class="footer-bottom">')
    if fb == -1:
        return None
    close = s.rfind("</div>", 0, fb)      # footer-grid 的闭合
    if close == -1:
        return None
    block = col("Travel Guides", GUIDES, "guides") + col("Company", COMPANY, "company")
    return s[:close] + block + "\n " + s[close:]


def sibling_block(city, fname):
    subs = sorted(f for f in existing
                  if is_subpage(f) and page_city(f) == city and f != fname)
    if len(subs) < 2:
        return None
    links = "".join(
        f'\n   <li><a href="{f}">{html.escape(topic_title(f))}</a></li>'
        for f in subs[:8])
    return f'''
 <div class="page-siblings" data-siblings>
  <div class="container">
   <div class="footer-title" style="margin-bottom:var(--space-4)">Other {html.escape(city_display(city))} Guides</div>
   <ul class="footer-links" style="display:flex;flex-wrap:wrap;gap:var(--space-4)">{links}
   </ul>
  </div>
 </div>
'''


def topic_title(f):
    from cw_common import get_title, clean_title
    s = read(os.path.join(ROOT, f))
    return clean_title(get_title(s))


if __name__ == "__main__":
    files = html_files()
    for f in files:
        if f in ("admin.html", "batch_download.html", "image_downloader.html",
                 "seo-swot-analysis.html"):
            continue
        p = os.path.join(ROOT, f)
        s = read(p)
        s2 = insert_footer_cols(s)
        if s2 and s2 != s:
            write(p, s2)
            stats["footer_cols"] += 1
            stats["links"] += len(GUIDES) + len(COMPANY)

    # 子页兄弟链接
    for f in files:
        if not is_subpage(f):
            continue
        p = os.path.join(ROOT, f)
        s = read(p)
        if "data-siblings" in s:
            continue
        city = page_city(f)
        blk = sibling_block(city, f)
        if not blk:
            continue
        m = re.search(r"<footer[^>]*>", s)
        if m:
            s = s[:m.start()] + blk + s[m.start():]
            write(p, s)
            stats["sibling_blocks"] += 1
            continue
        # 没有 footer 的页面：插到 </body> 前
        mb = s.rfind("</body>")
        if mb != -1:
            s = s[:mb] + blk + s[mb:]
            write(p, s)
            stats["sibling_blocks"] += 1

    print(json.dumps(stats, ensure_ascii=False, indent=2))

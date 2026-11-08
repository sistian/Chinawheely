"""给 prices.html / thank-you.html / manage-order.html 补上 js/analytics.js 埋点接入。

幂等：已存在则跳过。
只处理「对外可见或转化相关」的页面；admin / batch_download / image_downloader /
seo-swot-analysis 属于内部工具或 noindex 文档，不埋点。
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = [
    "prices.html",       # 可索引的总览页
    "thank-you.html",    # 订单提交后的落地页（转化闭环）
    "manage-order.html", # 客户自助查单（noindex 但仍是转化链路）
]

TAG = '<script src="js/analytics.js" defer></script>'


def inject(path):
    with open(path, encoding="utf-8") as f:
        html = f.read()
    if "js/analytics.js" in html:
        return "skip"
    if "</body>" not in html:
        return "no-body"
    # 插在最后一个 </body> 之前，保持与其它页一致的写法
    idx = html.rfind("</body>")
    new = html[:idx] + "  " + TAG + "\n" + html[idx:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return "ok"


def main():
    for name in TARGETS:
        p = os.path.join(REPO, name)
        if not os.path.exists(p):
            print(f"{name:22s} MISSING")
            continue
        print(f"{name:22s} {inject(p)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

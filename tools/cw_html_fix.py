#!/usr/bin/env python3
"""
修复站点原有的 HTML 损坏（生成器 bug，非本次改动引入）
  A. 重复的 hero-lead 段落，首词被替换成碎片：'<divre/dilore/lore/dore/...' → 整段删除
     例："...Explore Ankang in comfort.</p> <divre Ankang in comfort. </p>" → 保留前半句，删碎片段
  B. '<divclass="divider">' → '<div class="divider">'
  C. '<divdiv class="container">' → '<div class="container">'
幂等：可重复执行。
"""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cw_common import ROOT, read, write, html_files

stats = {"dup_removed": 0, "divclass": 0, "divdiv": 0, "pages": 0}
# 重复碎片段：< 碎片 空格 城市名 in comfort. 空格 </p>
DUP = re.compile(r"\s*<[a-zA-Z]+ ([A-Z][a-zA-Z\-]+) in comfort\.\s*</p>")
# 站点原有损坏：好句 "...in comfort.</p>" 之后紧跟一段碎片重复句
# 碎片形态： '<div ore' / '<div clre' / '<div class= ' / '<div ce' / '. Explore' 等
DUP2 = re.compile(
    r"(in comfort\.</p>)(\s*)(?:<div\s+[a-zA-Z=\s]{0,12}|\. Explore)?\s*"
    r"[A-Z][a-zA-Z\-]+\s+in comfort\.\s*</p>")

if __name__ == "__main__":
    for f in html_files():
        p = os.path.join(ROOT, f)
        s = read(p)
        o = s
        s, n = DUP.subn("", s)
        stats["dup_removed"] += n
        s, n2 = DUP2.subn(r"\1", s)
        stats["dup_removed"] += n2
        if '<divclass="' in s:
            c = s.count('<divclass="')
            s = s.replace('<divclass="', '<div class="')
            stats["divclass"] += c
        if '<divdiv class="' in s:
            c = s.count('<divdiv class="')
            s = s.replace('<divdiv class="', '<div class="')
            stats["divdiv"] += c
        # 模板 bug：<section> 在 </main> 之后才闭合 → 对调
        s, ns = re.subn(r"</main>(\s*)</section>", r"</section>\1</main>", s)
        if ns:
            stats["section_swapped"] = stats.get("section_swapped", 0) + ns
        # 尾部截断：</html> 之后还有残留内容（原始仓库遗留）→ 截断
        h = s.find("</html>")
        if h != -1 and s[h + 7:].strip():
            s = s[:h + 7] + "\n"
            stats["truncated_tail"] = stats.get("truncated_tail", 0) + 1
        # page-siblings 块必须在 </body> 之前
        if "data-siblings" in s:
            mblk = re.search(r'\n <div class="page-siblings" data-siblings>.*?\n </div>\n </div>\n', s, re.S)
            ib = s.find("</body>")
            if mblk and ib != -1 and mblk.start() > ib:
                blk = mblk.group(0)
                s = s[:mblk.start()] + s[mblk.end():]
                ib = s.find("</body>")
                s = s[:ib] + blk + s[ib:]
                stats["siblings_moved"] = stats.get("siblings_moved", 0) + 1
        if s != o:
            write(p, s)
            stats["pages"] += 1
    print(json.dumps(stats, ensure_ascii=False, indent=2))

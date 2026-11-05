# Chinawheely 站点诊断报告
**日期：2026-11-05　范围：全站 517 个 HTML 页 + api.chinawheely.com**
**方法：全部基于脚本实测 + 权威词条核实，非抽样估计。工具见 `tools/cw_*.py`**

---

# 一、城市页信息准确性

## 1.1 已核实「正确」的部分（无需改动）

| 检查项 | 方法 | 结果 |
|---|---|---|
| 省份归属 | 394 条权威地级市→省表 vs `city_facts` vs 页面正文标注，三方交叉 | **0 冲突** ✅ |
| 机场 IATA | `city_facts` 的真实机场码 vs 页面出现的 IATA | **全部一致** ✅ |
| JSON-LD 占位/空值 | 全站正则扫描 `""/null/{}/TBD/Unknown/PLACEHOLDER` | **0 处** ✅ |
| 模板 token 残留 | `{{}}`/`{Xxx}`/`City_Suffix`/`Attraction_B`/`Professional_*` | **仅 1 处**（`image_downloader.html` 的 `{cityname}`，该页已被 robots 屏蔽，低优先级） |
| 占位人口/面积 | 22 个无 facts 城市已删除占位值 | 已清 ✅ |
| 串城地标扫描 | 79 个独占地标 × 全站，**词边界匹配 + 行程语境过滤** | 34 处命中 → **33 处人工复核为合理表述**，1 处真错（见下） |

### 33 处「命中」为何都是误报（已逐条核实）

| 命中 | 实际 | 判定 |
|---|---|---|
| `jiayuguan` → Great Wall | 嘉峪关是长城西端起点 | ✅ 正确 |
| `fuyang` → West Lake | 阜阳「颍州西湖」 | ✅ 正确 |
| `fuzhou` → West Lake Park (Xihu) | 福州确有「西湖公园」 | ✅ 正确 |
| `nanjing` → Slender West Lake | 扬州「瘦西湖」，跨城一日游 | ✅ 正确 |
| `nanyang` → Wuhou Shrine | 南阳武侯祠（诸葛亮的庙） | ✅ 正确 |
| `dandong` → Tiger Mountain Great Wall | 丹东虎山长城 | ✅ 正确 |
| `chuzhou` → Confucius Temple | 「下午去南京秦淮/孔庙区」行程表述 | ✅ 正确 |
| `jiuquan` → Mogao Caves | 敦煌属酒泉市辖 | ✅ 正确 |
| `wuhan` → West Lake | 「是杭州西湖的 6 倍」对比句 | ✅ 正确 |
| `changchun` → Lu Xun Academy | 明确写了 "in Shanghai" | ✅ 正确 |
| `pingliang` → Hui Muslim quarter | 平凉回族街区，与西安无关 | ✅ 正确 |
| `shanghai-photo-spots` → the Bund | 上海自己的 | ✅ 正确（子页 slug 不等于城市名导致误判） |
| `hangzhou/chongqing/qingdao/…-day-trips` | 都是**母城自己的**景点 | ✅ 正确（同一原因误判） |

---

## 1.2 🔴 发现 1 处真实错误（需修）

### `changchun.html` —— 冰雪大世界是哈尔滨的，长春被写错了

**现状文案：**
> "Changchun is internationally famous for its **Ice and Snow World (冰雪大世界)**, a winter wonderland of enormous ice sculptures illuminated in brilliant colors. The main venue is at Changchun **Jingyuetan Ice and Snow World**."

**三条独立证据链：**

1. **中文维基条目名直接就叫「哈尔滨冰雪大世界」** — `zh.wikipedia.org/wiki/冰雪大世界` 重定向到 `哈尔滨冰雪大世界`。哈尔滨冰雪大世界是全球规模最大的冰雪主题乐园。
2. **长春净月潭词条里没有「冰雪大世界」** — `zh.wikipedia.org/wiki/净月潭` 记载的是：净月潭滑雪场（雪道 5 万㎡）、**瓦萨滑雪节**、**长春冰雪旅游节**（每年 11 月下旬至翌年 3 月滑雪期）。长春的冰雪项目叫**冰雪新天地**。
3. **英文维基 Changchun 现版本已经没有这句话** — 说明站点是从**一个已被修订掉的旧版本**抄来的（维基条目历史遗留错误）。

**为什么必须修（不只是"不好看"）：**
- 用户搜「冰雪大世界」落地页 = 哈尔滨，站却在长春页抢这个词 → **与 Google/百度 头部结果直接冲突**
- 事实性冲突会降低整站可信度（E-E-A-T），对旅游服务类站点是排名杀手
- 页面自身还写了 "internationally famous"，把一个哈尔滨的标签安到长春头上

**三个改法（请你选）：**

| 方案 | 改法 | 优点 | 缺点 |
|---|---|---|---|
| **A. 最小修正**（推荐） | `Ice and Snow World (冰雪大世界)` → `Ice and Snow New World (冰雪新天地)`，保留 Jingyuetan 定位 | 改动最小、事实正确 | 仍缺"国际知名"这层 |
| **B. 事实最稳** | 整段换成有词条支撑的三件事：**净月潭国家森林公园**（AAAAA）、**瓦萨滑雪节 Vasaloppet China**、**长春冰雪旅游节** | 每句都能溯源，可信度最高 | 需要重写 2-3 句 |
| **C. A + 消歧** | 在 B 基础上加一句：*"Do not confuse it with Harbin's Ice and Snow World, a separate and much larger venue."* | 既纠正又覆盖「冰雪大世界」这个搜索词 | 稍显刻意 |

> 我的建议：**B 或 C**。顺带一提，`harbin.html` 里的 Ice and Snow World 是**对的**，不要动。

---

## 1.3 🟠 canonical 与 og:url 不一致（9 页）

搜索引擎以 canonical 为准，og:url 只影响社交分享卡。两者不一致通常无害，但**在别名页/桩页上会让 Google 判为"信号矛盾"**，属于应修项：

| 页面 | canonical | og:url | 性质 |
|---|---|---|---|
| `hulunbeier.html` | `/eerduosi.html` | `/hulunbuir.html` | 🔴 别名桩页，两边指向**不同**城市 |
| `jdz.html` | `/jdz.html` | `/jingdezhen.html` | 🔴 同上 |
| `taizhou_zj.html` | `/taizhou_zj.html` | `/taizhou.html` | 🔴 **同名不同省**，最危险（可能把浙江台州信号给江苏台州） |
| `yichun-heilongjiang.html` | `/yichun-heilongjiang.html` | `/yichun_hlj.html` | 🟠 同上 |
| `yichun_jx.html` | `/yichun_jx.html` | `/yichun.html` | 🟠 同上 |
| `batch_download.html` | `/index.html` | 自身 | 🟢 已 noindex，低危 |
| `image_downloader.html` | `/index.html` | 自身 | 🟢 已 noindex |
| `seo-swot-analysis.html` | `/index.html` | 自身 | 🟢 已 noindex |

**建议**：别名页/桩页统一 `og:url = canonical`（社交分享指向正牌页是好事）。`taizhou_zj` 和 `yichun_*` 三个必须优先修。

---

# 二、标题层级与正文深度

## 2.1 现状总表

| | 城市页 | 主题页 |
|---|---|---|
| 页数 | **374** | **143** |
| H1 | 374 页各 1 个 ✅ | 143 页各 1 个，但 **66 个在 `<main>` 外** 🟠 |
| H2 | 平均 **11.6** 个 ✅ | 平均 **3.3** 个 🟠 |
| H3 | 平均 **10.1** 个 ✅（仅 1 页无 H3） | **114/143 页完全没有 H3** 🔴 |
| 正文字数 | 平均 **2396** 词 ✅ | 平均 **505** 词 🔴 |
| 最薄页 | 约 2400 词 | **28 个 <100 词**、39 个 <200 词 🔴 |

**结论：城市页基本达标，短板全在主题页。**

### 主题页的问题长什么样

`dalian-food-shopping.html`（全文 81 词）：
```
H1  Dalian Food & Shopping Guide | Local Cuisine & Best Markets
H2  Overview: Food & Shopping in Dalian
H4  🍜 seafood                    ← 跳过了 H3
H4  🍜 savoury potato jelly
H4  🍜 Dalian savoury potato jelly
H2  Where to Shop in Dalian
```
- **H2 → H4 直接跳级**，H3 层完全缺失
- 正文只有 81 词 → **soft-404 风险**：Google 会"抓取但不收录"
- 同类：`xiamen-best-time.html` 只有 **51 词**

### 跳级统计（全站）

| 问题 | 页数 |
|---|---|
| H2→H4 跳级（跳过 H3） | **451 页** |
| 全文无 H3 | **115 页**（全是主题页） |
| H1 在 `<main>` 外 | **66 页**（全是主题页） |
| 空标题 | 1 |
| 标题过长 >110 字 | **0** ✅ |
| 多个 H1 | **0** ✅ |

## 2.2 提升建议（按性价比排序）

### P0 —— 主题页 H4→H3 + 补正文（143 页，一次性解决 3 个问题）

**把 114 个主题页的 H4 改成 H3，并把正文补到 600–900 词。**

这样一页同时解决三件事：① 补齐 H1/H2/H3 三级结构 ② 解决 28 个 <100 词的 soft-404 ③ 提高该页类型的收录率。

**每个主题页建议的结构骨架**（H3 数量 ≥4）：
```
H1  {City} {Topic} | {钩子}
H2  Overview（80-120 词）
  H3  {子项1}  ← 30-60 词
  H3  {子项2}
  H3  {子项3}
H2  {第二个主块}
  H3  ...
H2  {第三个主块}
  H3  ...
```

**内容来源必须是真实信息**（已有数据源）：
- 气候/月度数据 → `workspace/best_time_data.json`（296 城真实逐月均温+降水）
- 景点/名吃 → `workspace/theme_sights.json`、`workspace/theme_food_shop.json`
- 城市基础事实 → `workspace/city_facts/*.json`（297 条）
- 13 种名茶的公认事实英文表述 → `workspace/tea_desc.py`
- ⚠ **没有真实数据的小城市，宁可只保留已有内容并标 noindex，也不要编造**

### P1 —— 城市页 H4→H3（保持层级连续，~340 页）

374 个城市页里只有 1 页完全无 H3（已经很好了），但仍有大量 H2→H4 跳级。把「Top Attractions」下的 H4（📍 798 Art District / 💧 Yellow River waterfront / 🏛 Famen Temple）改成 H3，层级就连续了。

> ⚠ 改 H4→H3 时要同步检查 CSS 选择器（`h4{...}`）和 `cw_audit.py` 的标签配平门禁，避免样式丢失。

### P1 —— H1 移进 `<main>`（66 页主题页）

主题页的 hero `<section class="hero">` 在 `<main>` 之外，导致**页面主内容从 `<main>` 才开始，H1 却不在其中**。语义上应该：
```html
<main>
  <section class="hero">
    <div class="container">
      <h1>…</h1>   ← 移进来
    </div>
  </section>
  …
</main>
```
Google 的 H1 提取不依赖 `<main>`，所以**这不是收录阻塞项**，但属于语义正确性问题，且改起来机械、零风险。

### P2 —— 过短标题（1305 个）

多数是季节名 `<h4>Spring</h4>` / `<h4>Summer</h4>`。改成 `Spring in Ankang` / `Best time for a spring visit` 之类更利于语义与长尾词覆盖。

### P2 —— H1 长度优化

抽查下来 H1 普遍是 `City + 主题 + | 钩子` 的格式，质量不错，**无需大改**。但建议把核心关键词前置（`Dalian Food & Shopping Guide` 已合格）。

---

# 三、为什么没被 Google 收录 —— 诊断与策略

## 3.1 技术层面：基本健康（这些都**不是**问题）

| 检查项 | 结果 |
|---|---|
| robots.txt | ✅ 无误封，`Allow: /`，已声明 sitemap |
| sitemap.xml | ✅ 491 条 URL，抽样 41 个**全部 200** |
| 主题页收录 | ✅ 115/115 全在 sitemap，**0 个带 noindex** |
| 零入链页 | ✅ 14 个，**全部是 noindex 页**（正确） |
| canonical 缺失 | ✅ **0 页**缺失 |
| 多个 H1 | ✅ 0 |
| 页面体积 | ✅ 494/517 页 <80KB（均价 41KB） |
| 首页图片 | ✅ 162KB |
| JSON-LD 语法 | ✅ 0 非法 |
| Open Graph | ✅ 99.8% 覆盖 |
| 城市页正文 | ✅ 平均 2396 词 |

## 3.2 🔴 真正的 4 个原因

### 原因 1（最关键）：**没有接入 Google Search Console**

站上 `grep -ri "google-site-verification\|G-XXXX\|UA-"` → **0 结果**。

这一条直接造成：
- ❌ **sitemap 从未提交**给 Google（sitemap 只在 robots.txt 里声明了路径，**Google 不会自动去读 robots.txt 里那行 Sitemap: 除非你提交过**）
- ❌ 没有「网址检查」工具 → 无法知道某页是"已发现未抓取"/"已抓取未收录"/"已排除"
- ❌ 没有「网页索引」覆盖率报告 → **无法量化到底哪些页被排除、为什么**
- ❌ 没有任何"已编入索引"数据 → 你现在看到的"很多页没收录"是**猜测，不是诊断**

> **这是必须今天就做的第 1 件事。** 没有它，后面所有 SEO 动作都是盲猜。

### 原因 2：没有 GA4 埋点

同样 `0 结果`。没有 GA4 就无法：
- 判断哪些页真的有人访问（区分"高质量但没排名" vs "没人要的低质页"）
- 用 GSC 的「页面洞察」交叉验证
- 做后续 A/B 实验（改标题/改内容后看点击率变化）

### 原因 3：重复内容比例过高 —— 58% 的页面在重复簇里

**聚类结果（阈值 0.45）**：

| 指标 | 数值 |
|---|---|
| 参与比对页面 | 516 |
| 重复边 | **2820** |
| 重复簇 | 10 个 |
| **处于重复簇的页面** | **301 页（58%）** |
| 最大一簇 | **230 页**（ankang / anqing / anyang / baise / bitu / changdou / …） |
| 次大簇 | 28 个 `airport-transfer-to-*` 页（互相相似度 **0.80**） |
| 第三簇 | 13 个 `*-tea-culture.html`（**0.64**） |

**段落级同质度排行（真实数据）**：

| 页数 | 同质度 | 均词数 | 模板 |
|---|---|---|---|
| 20 | **0.83** | 121 | `visa & entry information for {C}` |
| **304** | **0.77** | 92 | `useful chinese phrases for {C}` |
| **301** | **0.73** | 111 | `travel essentials for your {C} trip` |
| 51 | 0.62 | 572 | `transparent pricing in {C}` |
| **241** | 0.55 | **644** | `what your {C} ({P}) ride will cost`（价目表） |
| **271** | 0.55 | **428** | `tea culture & teahouse guide in {C}` |
| 286 | 0.38 | 152 | `food & shopping in {C}` |
| 326 | 0.36 | 155 | `{C} local secrets` |
| 285 | 0.29 | 164 | `getting to {C}: airports & railway stations` |
| 263 | 0.29 | 98 | `intangible cultural heritage…` |

分层结果：
- **高度模板（≥0.6）：7 类模板，覆盖 9% 正文**
- **中度模板（0.3–0.6）：8 类模板，覆盖 38% 正文**
- 基本独有（<0.3）：52% ← **这部分是你的优质资产**

✅ **真正独有的内容**（sim <0.2，值得保护和扩写）：
`top {C} attractions` (0.06)、`popular {C} airport transfer routes` (0.10)、`day trips from {C}` (0.14)、`best time to visit {C}` (0.16)、`{C}'s best photo spots` (0.19)、`popular {C} routes` (0.19)

**结论：Google 抓到那 230 个几乎一样的城市页时，只会保留（少数）一个。** 这就是"很多页没收录"的直接机制。

> ⚠ 注意：`useful chinese phrases` / `travel essentials` / `visa` 这三段**本身不是错**，通用旅行信息是合理内容。问题在于 **304/301 页各自带一份完全一样的副本**，等于把同一篇文章复制了 300 遍。正确做法见阶段 2。

### 原因 4：主题页过薄 → soft-404

28 个主题页 <100 词、39 个 <200 词。Google 抓到 51 词的 `xiamen-best-time.html`，会判定为"低价值/软 404" → **抓取但不收录**。这在 GSC 里会显示为「已抓取，未编入索引」。

### 3.3 其它已知但次要的因素

- **别名页只能 noindex 不能 301**：GitHub Pages 没有 301 能力，同名不同省城市（taizhou_zj / taizhou、yichun_*）被强行 noindex + 自指 canonical，**信号无法合并**，等于放弃了这些词的排名机会。
- **没有 Review schema**（0%），旅游服务类站点缺 E-E-A-T 佐证。
- **无 hreflang 的页有 174 个**（全站 517 页中 343 页有 en + x-default）。站点是纯英文，hreflang=en 自指其实没有实际价值，**可全站统一加上（一次性），也可以确认不需要**。
- **词库 14461 条只覆盖 23 个城市**，扩城排序缺乏真实 query 数据支撑。

---

# 四、SEO 执行路线图

## 阶段 0：立刻做（本周，约 2 小时）—— 不做这步，后面全是盲猜

| # | 动作 | 说明 |
|---|---|---|
| 1 | **接 Google Search Console** | 走 DNS TXT 验证（`google-site-verification` 记录），比 HTML 文件验证更稳（GitHub Pages 也能放文件，但 DNS 不会被抢注） |
| 2 | **在 GSC 提交 sitemap.xml** | `https://www.chinawheely.com/sitemap.xml`，提交后可用「网址检查」批量测试 |
| 3 | **接 GA4** | 装 GA4 会自动打通 GSC 的「网页索引 / 页面洞察」，两者一起做效果最好 |
| 4 | **看 GSC 覆盖率报告** | 重点看 4 类：**已发现但未编入索引 / 已抓取但未编入索引 / 重复或规范 / 已排除**，把"已排除"的原因截图分类 → 这才是真正的诊断 |
| 5 | **用「网址检查」批量测 20 个关键页** | 首页 + 5 大城市页 + 5 个主题页 + 5 个有价城市页 + 5 个小城页，看它们各自卡在哪一环 |

> 成本：GSC 免费、GA4 免费。**这一步的信息价值 > 所有内容改动的总和。**

## 阶段 1：技术修复（第 2–3 周）

| # | 动作 | 目的 |
|---|---|---|
| 6 | **补齐主题页正文到 600–900 词 + H4→H3** | 解决 soft-404 + 补齐三级标题 + 提升主题页收录 |
| 7 | **修 9 页 canonical ≠ og:url** | 优先 `taizhou_zj`、`yichun-*`、`hulunbeier`、`jdz` |
| 8 | **修 changchun 冰雪大世界** | 消除事实冲突（见 1.2） |
| 9 | **补齐 22 个无 facts 城市页的 JSON-LD 复查** | 防 schema 空洞 |
| 10 | **修 66 页 H1 到 `<main>` 内** | 语义正确性 |
| 11 | **301 重定向能力** ← 需要决策 | GitHub Pages 没有 301。**建议**：把站点迁到 Vercel（你已有 `vercel.json` 和现成部署流程），用 `redirects` 做真 301，把别名页/重复主题页的信号合并到正牌页。收益比继续写内容大得多 |

### 关于第 11 条的具体建议

用 301 把这些页合并掉（能真正传递排名信号，而不是像现在这样 noindex 掉）：
- 17 个别名桩页 → 对应正牌页（`hulunbeier`→`eerduosi`、`taizhou_zj`→`taizhou`、`yichun_hlj`→`yichun_hlj`…）
- 28 个 `airport-transfer-to-*` 里相似度 >0.75 的 → 合并到母城页或互为唯一
- 13 个 `*-tea-culture` 里相似度 >0.6 的 → 合并或重写差异化

## 阶段 2：内容去模板化（第 4–6 周）

| # | 动作 | 预期 |
|---|---|---|
| 12 | **把 3 个通用大段抽成全站单页** | `useful chinese phrases`(304页×92词)、`travel essentials`(301页×111词)、`visa & entry`(20页×121词) → 各做成一个权威长页（如 `/travel-tips/`），城市页只留 1 段 30 词的差异化内容 + 链接。**直接砍掉约 6 万词重复文本** |
| 13 | **价目表瘦身** | `what your {C} ride will cost` 每页 644 词 × 241 页 → 缩到 ≤200 词，完整 53 城价目留在已有的 `/prices.html`，城市页只展示本城 + 3 个对比城 |
| 14 | **`tea culture` 段差异化**（271 页 × 428 词，sim 0.55） | 每城只写本城那一种茶 + 冲泡方式，其余 12 种茶引流到总页 |
| 15 | **扩写「真独有」的 6 个段落** | `top attractions`(0.06)、`best photo spots`(0.19)、`day trips`(0.14)、`best time`(0.16)、`popular routes`(0.19)、`airport routes`(0.10) —— 这 6 段是你唯一的护城河，加厚它们比再加页数有用 |
| 16 | **做内容集群（Topic Cluster）** | hub = 城市页；spoke = 主题页；双向内链 + 面包屑（已有）。每个主题页链接回母城页，每个母城页列出其主题页 |
| 17 | **加 FAQPage / Review schema** | 目前 Review schema 0%，FAQ 需核实 |

## 阶段 3：持续（长期）

| # | 动作 | 说明 |
|---|---|---|
| 18 | **真实外链** | Google 对旅游服务的排名主要看**第三方提及**（小红书/马蜂窝/Tripadvisor/Reddit/YouTube/本地媒体），不是自建外链。持牌 L-HUB-101603 是真实背书，值得主动做 |
| 19 | **按 GSC 真实 query 排扩城顺序** | 词库 14461 条只覆盖 23 城。拿到 GSC 真实 query 后，用 `city_data.json` + `gen_*.py` 生成流水线扩城，**不要手工造页** |
| 20 | **性能** | 预加载 LCP 图、补 width/height、扩 WebP（`prices.html` 331KB 偏重） |
| 21 | **每季度复查** | 重新跑本次这 6 个审计脚本，把 FAIL 门禁并进 CI（`.github/workflows/ci.yml` 已有） |

---

# 五、给你的决策清单（需要你拍板）

| # | 决策点 | 我的建议 | 影响面 |
|---|---|---|---|
| 1 | changchun 冰雪大世界怎么改 | 方案 **B 或 C**（换冰雪新天地/净月潭/瓦萨滑雪节） | 1 页 |
| 2 | 是否把站点从 GitHub Pages 迁到 Vercel | **迁**，为了真 301 合并信号 | 全站，是阶段 1 收益最高的一项 |
| 3 | 143 个主题页是"补内容"还是"合并/删除" | **混合**：有真实数据可写的补到 600–900 词；没有的合并到母城页并 301 | 143 页 |
| 4 | `useful chinese phrases` 等 3 个通用段 | 抽成 1 个全站长页，城市页留短版 + 链接 | 砍 6 万词重复 |
| 5 | hreflang | 站点纯英文，**建议全站统一加 en + x-default**（或干脆全删） | 174 页 |
| 6 | 报价单口径（银川/台州） | 维持「Excel 显式值优先」，不动 | — |

---

## 附录：本次新增的审计工具（可复现，全部只读）

| 工具 | 作用 |
|---|---|
| `tools/cw_heading_audit.py` | H1/H2/H3 数量 + 词数分布 |
| `tools/cw_index_audit.py` | robots / sitemap / noindex / canonical / og:url |
| `tools/cw_index_deep.py` | sitemap 状态码抽样 / 主题页收录 / 孤儿页 / 页面体积 |
| `tools/cw_accuracy_audit.py` | 串城扫描 / 省份 / IATA / 占位符 / JSON-LD 空值 |
| `tools/cw_dup_clusters.py` | 近似重复聚类（5-gram Jaccard + 并查集） |
| `tools/cw_template_analysis.py` | 段落级模板化排行 |
| `tools/cw_section_diff.py` | 按 H2 分段的两页差异对比 |
| `tools/cw_heading_rules.py` | 标题层级规范（跳级/空/长短） |

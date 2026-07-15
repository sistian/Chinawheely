# City Landing Page Template (For Batch Generation)

## 已完成的主要城市 (8个)

| 城市 | 文件 | 三级域名建议 | 状态 |
|------|------|-------------|------|
| 北京 | beijing.html | beijing.chinawheely.com | ✅ 完成 |
| 上海 | shanghai.html | shanghai.chinawheely.com | ✅ 完成 |
| 西安 | xian.html | xian.chinawheely.com | ✅ 完成 |
| 成都 | chengdu.html | chengdu.chinawheely.com | ✅ 完成 |
| 广州 | guangzhou.html | guangzhou.chinawheely.com | ✅ 完成 |
| 杭州 | hangzhou.html | hangzhou.chinawheely.com | ✅ 完成 |
| 深圳 | shenzhen.html | shenzhen.chinawheely.com | ✅ 完成 |
| 武汉 | wuhan.html | wuhan.chinawheely.com | ✅ 完成 |

## 待完成的剩余城市 (30+)

Chongqing, Nanjing, Suzhou, Qingdao, Xiamen, Kunming, Tianjin, Dalian, Changsha, Zhengzhou, Harbin, Jinan, Fuzhou, Hefei, Nanchang, Guiyang, Lanzhou, Taiyuan, Shijiazhuang, Nanning, Haikou, Urumqi, Lhasa, Yinchuan, Xining, Hohhot, Changchun, Shenyang, Wenzhou, Ningbo, Wuxi, Foshan, Zhuhai, Macau, etc.

## 每个城市页面包含的内容模块

1. **SEO Head** — Title, Description, Canonical, OG, Twitter Card, Schema.org (TravelAgency + City + Breadcrumb)
2. **城市概况** — 面积、人口、名字由来、幸福指数、地铁交通、大学教育、自然资源
3. **景点介绍** — 6个主要景点，含图标和描述
4. **热门路线** — 4条接送路线（机场到市区、景点往返等），含价格
5. **美食和购物** — 各4个推荐
6. **服务CTA** — 预订按钮 + WhatsApp联系方式
7. **Footer** — 导航链接

## 三级域名配置说明

将每个城市页面配置为独立的三级域名：

```
beijing.chinawheely.com    →  beijing.html
shanghai.chinawheely.com   →  shanghai.html
xian.chinawheely.com       →  xian.html
chengdu.chinawheely.com    →  chengdu.html
guangzhou.chinawheely.com  →  guangzhou.html
hangzhou.chinawheely.com   →  hangzhou.html
shenzhen.chinawheely.com   →  shenzhen.html
wuhan.chinawheely.com      →  wuhan.html
```

**DNS配置**（以Cloudflare为例）：
- 类型：CNAME
- 名称：beijing
- 目标：chinawheely.com
- TTL：Auto

**服务器配置**（Nginx示例）：
```nginx
server {
    listen 80;
    server_name beijing.chinawheely.com;
    root /var/www/chinawheely;
    index beijing.html;
    location / {
        try_files $uri $uri/ =404;
    }
}
```

## 已生成的Favicon文件

- `favicon.png` (120×120)
- `favicon-32x32.png` (32×32)
- `apple-touch-icon.png` (180×180)

这些文件被所有城市页面共享引用。

## Schema.org 结构化数据类型

每个城市页面包含：
- `TravelAgency` — 城市服务商信息
- `City` — 城市基本信息（人口、面积）
- `BreadcrumbList` — 面包屑导航
- `Organization` — 公司信息

## 建议的下一步

1. **部署三级域名** — 在DNS中为8个已完成的配置域名
2. **Google Search Console** — 提交每个城市页面的sitemap
3. **分批生成剩余城市** — 使用现有模板，每次生成5-10个城市
4. **添加城市图片** — 为每个城市准备高质量图片（hero背景）

## 批量生成脚本（可选）

如果需要批量生成剩余城市，可以使用Python脚本基于模板替换城市特定内容。模板文件已保存在城市页面中，可复制任意一个作为基础模板。

## 文件清单

```
Chinawheely-Website/
├── index.html          ← 已更新城市卡片链接
├── beijing.html        ← 新
├── shanghai.html       ← 新
├── xian.html           ← 新
├── chengdu.html        ← 新
├── guangzhou.html      ← 新
├── hangzhou.html       ← 新
├── shenzhen.html       ← 新
├── wuhan.html          ← 新
├── favicon.png         ← 新
├── favicon-32x32.png   ← 新
├── apple-touch-icon.png← 新
├── styles.css          ← 现有（共享样式）
├── scripts.js          ← 现有（共享脚本）
└── images/             ← 现有图片
```

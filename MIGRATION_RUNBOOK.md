# Chinawheely → Vercel 迁移执行手册

> 状态：**代码与配置 100% 就绪，只差你改一条 DNS 记录**
> 准备日期：2026-11-05　提交：`35dcc37`

---

## 一、为什么迁

GitHub Pages 没有 301 重定向能力 → 17 个别名页只能 `noindex`，**排名信号无法合并**。
迁到 Vercel 后用 `vercel.json` 的 `redirects` 拿真 301。

**额外收益（已实测）**：Vercel 会通过响应头下发 CSP / X-Frame-Options / HSTS /
Referrer-Policy / Permissions-Policy —— GitHub Pages 做不到（只能塞 `<meta>`，且
`frame-ancestors` 在 meta 里会被忽略）。这一并完成了「CSP 移到服务器层」这个挂了很久的待办。

---

## 二、已完成并验证的部分（不需要你做任何事）

| # | 项目 | 状态 |
|---|---|---|
| 1 | `vercel.json` 写入 14 条 `statusCode: 301` 重定向 | ✅ 线上实测 14/14 返回 301 |
| 2 | 14 个别名桩页 → 权威正牌页，映射表逐条校验（目标存在 / 目标可索引 / 非自我 / 非桩页） | ✅ |
| 3 | 5 个「同名不同省」真实城市页恢复索引（江苏泰州 / 黑龙江伊春 / 安徽宿州 / 江西抚州 / 陕西榆林） | ✅ |
| 4 | sitemap 491 → 496 | ✅ |
| 5 | 站内指向桩页的链接全部改为直指最终目标（首页城市卡等） | ✅ 全站 0 残留 |
| 6 | `www.chinawheely.com` + `chinawheely.com` 已加入 Vercel 项目 | ✅ |
| 7 | 迁移一致性检查：15/15 页字节一致、4/4 页 DOM 一致、23/23 资源可达 | ✅ |
| 8 | CSP 下无任何违规，booking 页 JS 正常渲染 | ✅ |
| 9 | `/api/order` 404、`/api/quote` 200、CORS `*`、表单全用绝对 API URL | ✅ 无影响 |
| 10 | 审计门禁新增「同名不同省城市页」「301重定向表」「sitemap:死链」 | ✅ FAIL 0 / PASS 19 |

---

## 三、你要做的：改 1 条 DNS 记录（GoDaddy）

**只改 `www` 一条即可。** apex `chinawheely.com` 目前由 GitHub Pages 自动 301 到 www，
保持不动即可（它会跟着指到 Vercel）。

### 位置
GoDaddy → `chinawheely.com` → **DNS** → 找到 `www` 这条 **CNAME** 记录 → **改**

### 改成
| 类型 | 主机 | 指向 | TTL |
|---|---|---|---|
| CNAME | `www` | `71cacdf00f8feef8.vercel-dns-017.com` | 600 或默认 |

> ⚠ **必须是 CNAME，不要用 A 记录指 185.199.x.x**（那是 GitHub Pages）。
> ⚠ 这个目标与 `api.chinawheely.com` 现在用的**完全相同**，是之前后端迁移验证过的可靠路径。
> ⚠ **CNAME 冲突检查**：GoDaddy 若提示 `www` 记录与其它记录冲突，把那条冲突的 A/AAAA 删掉。

### 改完之后
1. 等 5–30 分钟生效（我已配置自动检查，会主动汇报）
2. Vercel 会自动签发证书（SAN 会含 `chinawheely.com` 和 `www.chinawheely.com`）
3. 生效后 GitHub Pages 就不再服务 www 了 —— **但仓库和 CNAME 文件保留**，随时能回滚

---

## 四、生效后我来做的事

1. 跑 `tools/verify_migration.py` 确认：DNS 指向 Vercel、证书是 Vercel 签发的、
   14 条 301 在 www 上真实生效、安全响应头已到位
2. 从仓库里**删除 14 个桩页 HTML**（现在留着是为了 GitHub Pages 期间不出 404；
   Vercel 的 redirect 优先于静态文件，所以留着也不影响 301 生效）
3. 把 CNAME 文件加回仓库 / 保留 GitHub Pages 作为灾备（可选）
4. 建议：接 Google Search Console + 提交 sitemap（这一步之前提过，是收录的第一优先级）

---

## 五、回滚方案（任何时候可做）

把 GoDaddy 的 `www` CNAME 改回 `sistian.github.io` 即可，1 分钟内生效。
站点结构、页面、链接都保留在 GitHub 仓库里，不依赖 Vercel。

---

## 六、注意事项

- **GitHub Pages 重新部署有延迟**（实测约 3–8 分钟）。迁移一致性检查时如果发现字节不一致，
  先等一会儿再判定，别误判成迁移问题。
- `.vercel.app` 域名**必须走本机代理**（直连不通），`www.chinawheely.com` 直连即可。
  Chrome 调试时：`--proxy-server=http://127.0.0.1:7897`（Vercel）/ `--no-proxy-server`（www）。
- Vercel 免费版单次部署上限 100MB；当前工作区约 36MB，安全。
- 前台目前是**命令行部署**（`vercel --prod`），还没接 GitHub 自动部署。
  迁完后建议在 Vercel 网页端给仓库装 GitHub App，恢复「push 即发布」的体验。

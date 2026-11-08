-- Chinawheely — 自建流量分析表 cw_analytics（替代 GA4）
--
-- 【需要你做一次】在 Supabase 控制台 → SQL Editor → 新建查询 → 粘贴本文件全部内容 → Run。
--   项目：https://supabase.com/dashboard/project/tybexleyjssmlqkuggdb/sql
-- 说明：
--   1) 本文件全程幂等（create table/index if not exists），重复执行安全。
--   2) 跑完后 api/analytics.js 才会开始落数据；未建表时前端静默降级，不会报错。
--   3) 本表只存事件维度（事件名 / 路径 / 城市 / referrer / 会话 id / UA / 业务 props），
--      不存姓名、邮箱、电话等任何个人身份信息（PII）。
--   4) 读取与写入全部走服务端 service_role（api/_lib/db.js），anon 角色无任何权限。

create table if not exists public.cw_analytics (
  id         bigserial primary key,
  ts         timestamptz not null default now(),
  event      text not null,          -- page_view / booking_start / booking_submit / ...
  path       text,                   -- 页面路径（含 query，上限 300 字符）
  city       text,                   -- 城市 slug（上限 80 字符）
  referrer   text,                   -- 来源站（上限 300 字符）
  session_id text,                   -- 前端会话随机 id（无 cookie、无指纹）
  ua         text,                   -- User-Agent（上限 200 字符）
  props      jsonb                   -- 业务维度（product / vehicle / hours ...）
);

-- 索引：后台面板按时间倒序取事件流、按事件名 / 城市聚合
create index if not exists cw_analytics_ts_idx    on public.cw_analytics (ts desc);
create index if not exists cw_analytics_event_idx on public.cw_analytics (event);
create index if not exists cw_analytics_city_idx  on public.cw_analytics (city);

-- 建议（可选）：保留 90 天数据。执行前请确认 Supabase 已开启 pg_cron / pg_cron 扩展。
-- select cron.schedule('cw_analytics_gc', '0 3 * * *', $$delete from public.cw_analytics where ts < now() - interval '90 days'$$);

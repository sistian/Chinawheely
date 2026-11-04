-- Chinawheely P4 — 订单表 cw_orders
-- 在 Supabase SQL Editor 中执行（tybexleyjssmlqkuggdb）
-- 设计要点：
--   * status 与 payment_status 分两层（服务状态 / 支付状态）
--   * quote_json 保存下单时的价格快照（调价不影响历史订单）
--   * manage_token 只存 sha256 哈希，明文仅出现在给客户的邮件链接里
--   * 全部读写走 service_role（服务端 API），anon 无任何权限

create table if not exists public.cw_orders (
  id                      bigserial primary key,
  ref                     text not null unique,                 -- CWO-YYYYMMDD-XXXXXXXX
  status                  text not null default 'pending',      -- pending/confirmed/in_service/completed/cancelled/no_show
  payment_status          text not null default 'unpaid',       -- unpaid/payment_submitted/paid/refunded/failed
  payment_method          text,                                 -- paypal / alipay / bank
  email                   text not null,
  phone                   text,
  customer_name           text,
  city                    text,
  product                 text,                                 -- airport / charter / intercity
  vehicle                 text,
  tier                    text,                                 -- 包车时长档（2h_35km 等）
  quote_json              jsonb,                                -- 价格快照（total/usd/lines/warnings）
  total_cny               numeric(10,2),
  total_usd               numeric(10,2),
  currency                text default 'CNY',
  pickup_date             date,
  pickup_time             text,
  pax                     integer,
  luggage                 integer,
  contact_json            jsonb,                                -- 行程细节（机场/酒店/航班等）
  notes                   text,
  manage_token_hash       text,
  manage_token_expires_at timestamptz,
  admin_note              text,
  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now()
);

-- 索引
create index if not exists cw_orders_created_idx   on public.cw_orders (created_at desc);
create index if not exists cw_orders_status_idx    on public.cw_orders (status);
create index if not exists cw_orders_pay_idx       on public.cw_orders (payment_status);
create index if not exists cw_orders_pickup_idx    on public.cw_orders (pickup_date);
create index if not exists cw_orders_email_idx     on public.cw_orders (email);

-- 约束：状态枚举
alter table public.cw_orders
  drop constraint if exists cw_orders_status_chk;
alter table public.cw_orders
  add constraint cw_orders_status_chk check (
    status in ('pending','confirmed','in_service','completed','cancelled','no_show')
  );

alter table public.cw_orders
  drop constraint if exists cw_orders_payment_chk;
alter table public.cw_orders
  add constraint cw_orders_payment_chk check (
    payment_status in ('unpaid','payment_submitted','paid','refunded','failed')
  );

-- RLS：service_role 全放行，anon/authenticated 一律拒绝
alter table public.cw_orders enable row level security;

drop policy if exists "cw_orders service all" on public.cw_orders;
create policy "cw_orders service all"
  on public.cw_orders
  for all
  to service_role
  using (true)
  with check (true);

-- 确认 anon 无权限（revoke 兜底）
revoke all on public.cw_orders from anon, authenticated;

-- updated_at 触发器
create or replace function public.cw_touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

drop trigger if exists cw_orders_touch on public.cw_orders;
create trigger cw_orders_touch
  before update on public.cw_orders
  for each row execute function public.cw_touch_updated_at();

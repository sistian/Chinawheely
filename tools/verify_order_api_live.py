#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上订单接口 + jsonb 行为验收（用 service_role 直接读库验证 jsonb 返回形态）。"""
import json, os, re, subprocess, sys, urllib.parse, urllib.request

API = "https://api.chinawheely.com/api"
ADMIN_API = "https://api.chinawheely.com/api/admin"
ENV = "/Users/w/Desktop/ChinaWiFiGo houduan 9.24/.env.local"
TEST_EMAIL = "cw-test-20261105@example.com"

ok = True


def env_val(k):
    for line in open(ENV, encoding="utf-8"):
        if line.strip().startswith(k + "="):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    return None


def post_json(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def get_json(url, headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}),
                                    timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def rest(method, path, body=None, key=None, base=None):
    url = f"{base}/rest/v1/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"apikey": key, "Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json",
                                          "Prefer": "return=representation"})
    with urllib.request.urlopen(req, timeout=60) as r:
        t = r.read().decode()
        return json.loads(t) if t.strip() else None


SB, KEY = env_val("SUPABASE_URL"), env_val("SUPABASE_SERVICE_ROLE_KEY")
print("=" * 66)
print("线上订单接口验收")
print("=" * 66)

# ---------- 1) 直接读库：确认 quote_json 的 jsonb 返回形态 ----------
print("\n【1】Supabase 返回的 quote_json 形态（这决定 safeParse 怎么写）")
rows = rest("GET", "cw_orders?select=ref,quote_json,total_cny&limit=3", key=KEY, base=SB)
for r in rows or []:
    q = r.get("quote_json")
    print(f"  {r.get('ref')}  total={r.get('total_cny')}")
    print(f"    quote_json 类型 = {type(q).__name__}")
    print(f"    quote_json 预览 = {json.dumps(q, ensure_ascii=False)[:150]}")
    if isinstance(q, dict):
        print("    ✅ 是已解析的对象 → safeParse 必须直接返回（修复前会 JSON.parse 抛异常 → null）")
        ok = True
    else:
        print("    ❌ 不是对象")
        ok = False
if not rows:
    print("  ⚠️ 库里没有订单（先下一单）")
    ok = False

# ---------- 2) admin 拿测试单 ref ----------
print("\n【2】取测试订单 ref")
st, r = post_json(f"{ADMIN_API}/session", {"email": "sistian@foxmail.com", "password": "F0wr5SU1hVglGy61"})
tok = r.get("token")
if not tok:
    print(f"  ❌ admin 登录失败 http={st}")
    sys.exit(1)
AUTH = {"Authorization": f"Bearer {tok}"}
st, r = get_json(f"{ADMIN_API}/orders?limit=30", AUTH)
orders = r.get("rows") or []
mine = [o for o in orders if o.get("email") == TEST_EMAIL]
print(f"  订单总数 {len(orders)}，测试单 {len(mine)}")
ref = mine[0]["ref"] if mine else (orders[0]["ref"] if orders else None)
print(f"  使用 ref = {ref}")

# ---------- 3) 状态码语义 ----------
print("\n【3】HTTP 状态语义")
if ref:
    st, r = get_json(f"{API}/order?ref={urllib.parse.quote(ref)}&token={'b' * 48}")
    print(f"  订单存在 + 错 token → http={st}")
    print(f"     body = {json.dumps(r, ensure_ascii=False)[:180]}")
    ok &= (st == 403)
    ok &= (r.get("code") == "TOKEN_MISMATCH")
    if st != 403:
        print("     ❌ 期望 403")
    else:
        print("     ✅ 403 + code=TOKEN_MISMATCH（修前是 500 'lookup failed'）")
st, r = get_json(f"{API}/order?ref=CWO-20261105-DEADBEEF&token={'a' * 48}")
print(f"  订单不存在 → http={st}  {'✅' if st == 404 else '❌'}")
ok &= (st == 404)
st, r = get_json(f"{API}/order?ref=NOPE&token={'a' * 48}")
print(f"  ref 格式错 → http={st}  {'✅' if st == 400 else '❌'}")
ok &= (st == 400)

# ---------- 4) 清理测试单 ----------
print("\n【4】清理测试单")
n = 0
for o in mine:
    rest("DELETE", f"cw_orders?ref=eq.{urllib.parse.quote(o['ref'])}", key=KEY, base=SB)
    n += 1
left = rest("GET", f"cw_orders?select=ref&email=eq.{urllib.parse.quote(TEST_EMAIL)}", key=KEY, base=SB)
print(f"  已删除 {n} 单，剩余测试单 {len(left or [])}")
ok &= (len(left or []) == 0)

print("\n" + "=" * 66)
print("✅ 全部通过" if ok else "❌ 有失败")
sys.exit(0 if ok else 1)

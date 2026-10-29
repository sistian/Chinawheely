// Chinawheely P1 — Supabase (PostgREST) 服务端客户端
// 零依赖实现：直接走 PostgREST，避免为 serverless 函数引入 @supabase/supabase-js
// 凭据来自 Vercel 环境变量：SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
// 未配置时自动降级为「纯邮件模式」，接口行为与改造前一致（不 500）

const SUPABASE_URL = (process.env.SUPABASE_URL || '').replace(/\/+$/, '');
const SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

function dbConfigured() {
  return Boolean(SUPABASE_URL && SERVICE_ROLE_KEY);
}

function baseHeaders(extra) {
  return Object.assign(
    {
      apikey: SERVICE_ROLE_KEY,
      Authorization: `Bearer ${SERVICE_ROLE_KEY}`,
      'Content-Type': 'application/json'
    },
    extra || {}
  );
}

/**
 * 调用 PostgREST
 * @returns {Promise<{ok:boolean, data:any, status:number, error:string}>}
 */
async function rest(path, options) {
  const opts = options || {};
  const method = opts.method || 'GET';
  const query = opts.query || '';
  const url = `${SUPABASE_URL}/rest/v1/${path}${query ? `?${query}` : ''}`;

  try {
    const res = await fetch(url, {
      method,
      headers: baseHeaders(opts.headers),
      body: opts.body ? JSON.stringify(opts.body) : undefined
    });
    const text = await res.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (e) {
        data = text;
      }
    }
    if (!res.ok) {
      const msg =
        (data && data.message) || (data && data.error) || `HTTP ${res.status}`;
      return { ok: false, data, status: res.status, error: String(msg) };
    }
    return { ok: true, data, status: res.status, error: '' };
  } catch (err) {
    return {
      ok: false,
      data: null,
      status: 0,
      error: (err && err.message) || 'db request failed'
    };
  }
}

function enc(value) {
  return encodeURIComponent(String(value == null ? '' : value));
}

/** 插入一行，返回 {ok, row, error} */
async function insert(table, row) {
  const res = await rest(table, {
    method: 'POST',
    query: 'select=*',
    headers: { Prefer: 'return=representation' },
    body: row
  });
  if (!res.ok) return { ok: false, row: null, error: res.error };
  const rowData = Array.isArray(res.data) ? res.data[0] : res.data;
  return { ok: true, row: rowData || null, error: '' };
}

/** 条件查询，返回行数组 */
async function select(table, query, limit) {
  let q = query || '';
  if (limit) q += (q ? '&' : '') + `limit=${encodeURIComponent(limit)}`;
  const res = await rest(table, { method: 'GET', query: q });
  if (!res.ok) return { ok: false, rows: [], error: res.error };
  return { ok: true, rows: Array.isArray(res.data) ? res.data : [], error: '' };
}

/** 按条件更新，返回更新后的行 */
async function update(table, query, patch) {
  const res = await rest(table, {
    method: 'PATCH',
    query: (query || '') + (query ? '&' : '') + 'select=*',
    headers: { Prefer: 'return=representation' },
    body: patch
  });
  if (!res.ok) return { ok: false, rows: [], error: res.error };
  return { ok: true, rows: Array.isArray(res.data) ? res.data : [], error: '' };
}

module.exports = { dbConfigured, rest, insert, select, update, enc };

import { supabase } from "./supabase";

const BASE = import.meta.env.VITE_API_BASE || "";

async function authHeader() {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(method, path, body) {
  const headers = { "Content-Type": "application/json", ...(await authHeader()) };
  const res = await fetch(`${BASE}/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
    }
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  listExchanges: () => request("GET", "/exchanges"),
  connectExchange: (payload) => request("POST", "/exchanges", payload),
  deleteExchange: (id) => request("DELETE", `/exchanges/${id}`),
  listStrategies: () => request("GET", "/strategies"),
  createStrategy: (payload) => request("POST", "/strategies", payload),
  updateStrategy: (id, payload) => request("PATCH", `/strategies/${id}`, payload),
  deleteStrategy: (id) => request("DELETE", `/strategies/${id}`),
  listTrades: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request("GET", `/trades${qs ? `?${qs}` : ""}`);
  },
  syncTrades: () => request("POST", "/trades/sync"),
  autoSyncTrades: async () => {
    const KEY = "cadence_last_sync";
    const last = Number(localStorage.getItem(KEY) || 0);
    if (Date.now() - last < 60000) return 0;
    localStorage.setItem(KEY, String(Date.now()));
    try {
      const r = await request("POST", "/trades/sync");
      return r.imported || 0;
    } catch {
      return 0;
    }
  },

  trends: () => request("GET", "/market/trends"),
  marketBases: (exchange = "kraken") => request("GET", `/market/bases?exchange=${exchange}`),

  portfolioSummary: () => request("GET", "/portfolio/summary"),
  portfolioHistory: () => request("GET", "/portfolio/history"),

  simulate: (params) => {
    const qs = new URLSearchParams(params).toString();
    return request("GET", `/simulate?${qs}`);
  },

  listNotifications: () => request("GET", "/notifications"),
  markNotificationsRead: (ids = null) => request("POST", "/notifications/read", { ids }),

  listGoals: () => request("GET", "/goals"),
  createGoal: (payload) => request("POST", "/goals", payload),
  deleteGoal: (id) => request("DELETE", `/goals/${id}`),

  taxSummary: (year) => request("GET", `/tax/summary${year ? `?year=${year}` : ""}`),
  taxExport: async (year) => {
    const res = await fetch(`${BASE}/api/tax/export?year=${year}`, {
      headers: { ...(await authHeader()) },
    });
    if (!res.ok) throw new Error("Export impossible");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cadence_releve_fiscal_${year}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

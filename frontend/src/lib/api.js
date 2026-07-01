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

  trends: () => request("GET", "/market/trends"),

  portfolioSummary: () => request("GET", "/portfolio/summary"),
  portfolioHistory: () => request("GET", "/portfolio/history"),

  simulate: (params) => {
    const qs = new URLSearchParams(params).toString();
    return request("GET", `/simulate?${qs}`);
  },

  listGoals: () => request("GET", "/goals"),
  createGoal: (payload) => request("POST", "/goals", payload),
  deleteGoal: (id) => request("DELETE", `/goals/${id}`),
};

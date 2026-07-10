const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  getDashboard: () => request("/dashboard"),
  getRecommendations: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/recommendations${qs ? `?${qs}` : ""}`);
  },
  getResources: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/resources${qs ? `?${qs}` : ""}`);
  },
  getCostSummary: () => request("/cost-summary"),
  getHistory: (limit = 30) => request(`/history?limit=${limit}`),
  triggerScan: () => request("/scan", { method: "POST" }),
  optimize: (body) => request("/optimize", { method: "POST", body: JSON.stringify(body) }),
};

import React, { useEffect, useState, useCallback } from "react";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";
import { api } from "../api/client.js";
import StatCard from "../components/StatCard.jsx";
import ScanButton from "../components/ScanButton.jsx";

const RISK_COLORS = { low: "#35c78a", medium: "#e8b339", high: "#ef5a6f", critical: "#c72c47" };

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [dash, recs] = await Promise.all([
        api.getDashboard(),
        api.getRecommendations(),
      ]);
      setSummary(dash);
      setRecommendations(recs);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const byRisk = ["low", "medium", "high", "critical"].map((risk) => ({
    name: risk,
    value: recommendations.filter((r) => r.Risk === risk).length,
  })).filter((d) => d.value > 0);

  const byType = Object.entries(
    recommendations.reduce((acc, r) => {
      const key = r.ResourceType.split(":")[0];
      acc[key] = (acc[key] || 0) + r.EstimatedMonthlySavings;
      return acc;
    }, {})
  ).map(([name, savings]) => ({ name, savings: Math.round(savings * 100) / 100 }));

  return (
    <div>
      <div className="toolbar">
        <h2>Dashboard</h2>
        <ScanButton onTriggered={load} />
      </div>

      {error && (
        <div className="error-banner">
          Couldn't reach the API ({error}). Is the backend running? See root README "Run locally".
        </div>
      )}

      {summary && (
        <div className="cards">
          <StatCard label="Open Findings" value={summary.total_open_findings} />
          <StatCard label="Potential Monthly Savings" value={`$${summary.total_potential_monthly_savings}`} variant="savings" />
          <StatCard label="Optimization Score" value={`${summary.optimization_score}/100`} variant="score" />
          <StatCard label="Critical Findings" value={summary.critical_findings} variant="critical" />
        </div>
      )}

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Potential Savings by Service ($/mo)</h3>
        {byType.length ? (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={byType}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262f45" />
              <XAxis dataKey="name" stroke="#8b93a7" fontSize={12} />
              <YAxis stroke="#8b93a7" fontSize={12} />
              <Tooltip contentStyle={{ background: "#171d2c", border: "1px solid #262f45" }} />
              <Bar dataKey="savings" fill="#4f8cff" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state">{loading ? "Loading…" : "No findings yet — run a scan to populate this."}</div>
        )}
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Findings by Risk</h3>
        {byRisk.length ? (
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={byRisk} dataKey="value" nameKey="name" innerRadius={60} outerRadius={90} paddingAngle={3}>
                {byRisk.map((entry) => (
                  <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />
                ))}
              </Pie>
              <Legend />
              <Tooltip contentStyle={{ background: "#171d2c", border: "1px solid #262f45" }} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state">{loading ? "Loading…" : "No findings yet."}</div>
        )}
      </div>
    </div>
  );
}

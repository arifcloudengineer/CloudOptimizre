import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";
import StatCard from "../components/StatCard.jsx";

export default function Savings() {
  const [summary, setSummary] = useState(null);
  const [top, setTop] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [costSummary, recs] = await Promise.all([
          api.getCostSummary(),
          api.getRecommendations(),
        ]);
        setSummary(costSummary);
        setTop([...recs].sort((a, b) => b.EstimatedMonthlySavings - a.EstimatedMonthlySavings).slice(0, 10));
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div>
      <div className="toolbar">
        <h2>Savings</h2>
      </div>

      {error && <div className="error-banner">Couldn't reach the API ({error}).</div>}

      {summary && (
        <div className="cards">
          <StatCard label="Potential Monthly Savings" value={`$${summary.total_potential_savings}`} variant="savings" />
          <StatCard label="Potential Annual Savings" value={`$${Math.round(summary.total_potential_savings * 12)}`} variant="savings" />
          <StatCard label="Optimization Score" value={`${summary.optimization_score}/100`} variant="score" />
          <StatCard label="Critical Findings" value={summary.critical_findings} variant="critical" />
        </div>
      )}

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Top 10 Most Expensive Resources</h3>
        {top.length ? (
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Resource</th>
                <th>Type</th>
                <th>Est. Monthly Savings</th>
              </tr>
            </thead>
            <tbody>
              {top.map((item, idx) => (
                <tr key={item.ResourceID}>
                  <td>{idx + 1}</td>
                  <td>{item.ResourceID}</td>
                  <td>{item.ResourceType}</td>
                  <td>${item.EstimatedMonthlySavings}/mo</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">{loading ? "Loading…" : "No findings yet — run a scan first."}</div>
        )}
      </div>
    </div>
  );
}

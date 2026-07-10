import React, { useEffect, useState, useCallback } from "react";
import { api } from "../api/client.js";
import RiskBadge from "../components/RiskBadge.jsx";

const SAFE_ACTIONS = new Set(["release", "tag", "delete"]);

export default function Recommendations() {
  const [items, setItems] = useState([]);
  const [risk, setRisk] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = risk ? { risk } : {};
      const data = await api.getRecommendations(params);
      setItems(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [risk]);

  useEffect(() => { load(); }, [load]);

  async function handleOptimize(item, dryRun) {
    setActionMsg(null);
    try {
      const res = await api.optimize({ resource_id: item.ResourceID, action: item.Action, dry_run: dryRun });
      setActionMsg(`${item.ResourceID}: ${res.detail}`);
      if (!dryRun) load();
    } catch (e) {
      setActionMsg(`${item.ResourceID}: ${e.message}`);
    }
  }

  return (
    <div>
      <div className="toolbar">
        <h2>Recommendations</h2>
      </div>

      <div className="filters">
        <select value={risk} onChange={(e) => setRisk(e.target.value)}>
          <option value="">All risk levels</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      {error && <div className="error-banner">Couldn't reach the API ({error}).</div>}
      {actionMsg && <div className="panel" style={{ fontSize: 13 }}>{actionMsg}</div>}

      <div className="panel">
        {items.length ? (
          <table>
            <thead>
              <tr>
                <th>Resource</th>
                <th>Type</th>
                <th>Condition</th>
                <th>Risk</th>
                <th>Est. Savings</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={`${item.ResourceID}-${item.ScanDate}`}>
                  <td>{item.ResourceID}</td>
                  <td>{item.ResourceType}</td>
                  <td>{item.Condition}<br /><span style={{ color: "var(--text-dim)" }}>{item.Recommendation}</span></td>
                  <td><RiskBadge risk={item.Risk} /></td>
                  <td>${item.EstimatedMonthlySavings}/mo</td>
                  <td>
                    {SAFE_ACTIONS.has(item.Action) ? (
                      <>
                        <button className="action-btn" onClick={() => handleOptimize(item, true)}>Dry run</button>
                        <button className="action-btn" onClick={() => handleOptimize(item, false)}>Apply</button>
                      </>
                    ) : (
                      <span style={{ color: "var(--text-dim)", fontSize: 12 }}>Manual review required</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">{loading ? "Loading…" : "No open recommendations for this filter."}</div>
        )}
      </div>
    </div>
  );
}

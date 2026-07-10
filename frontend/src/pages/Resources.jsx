import React, { useEffect, useState, useCallback } from "react";
import { api } from "../api/client.js";
import RiskBadge from "../components/RiskBadge.jsx";

const TYPE_PREFIXES = ["", "EC2", "EBS", "EIP", "RDS", "S3", "ELB", "NAT"];

export default function Resources() {
  const [items, setItems] = useState([]);
  const [type, setType] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = type ? { resource_type: type } : {};
      const data = await api.getResources(params);
      setItems(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [type]);

  useEffect(() => { load(); }, [load]);

  return (
    <div>
      <div className="toolbar">
        <h2>Resources</h2>
      </div>

      <div className="filters">
        <select value={type} onChange={(e) => setType(e.target.value)}>
          {TYPE_PREFIXES.map((t) => (
            <option key={t} value={t}>{t || "All types"}</option>
          ))}
        </select>
      </div>

      {error && <div className="error-banner">Couldn't reach the API ({error}).</div>}

      <div className="panel">
        {items.length ? (
          <table>
            <thead>
              <tr>
                <th>Resource ID</th>
                <th>Type</th>
                <th>Region</th>
                <th>Status</th>
                <th>Risk</th>
                <th>Last Scanned</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={`${item.ResourceID}-${item.ScanDate}`}>
                  <td>{item.ResourceID}</td>
                  <td>{item.ResourceType}</td>
                  <td>{item.Region}</td>
                  <td>{item.Status}</td>
                  <td><RiskBadge risk={item.Risk} /></td>
                  <td>{item.ScanDate?.slice(0, 19).replace("T", " ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">{loading ? "Loading…" : "No resources scanned yet."}</div>
        )}
      </div>
    </div>
  );
}

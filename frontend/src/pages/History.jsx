import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { api } from "../api/client.js";

export default function History() {
  const [scans, setScans] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getHistory(30);
        setScans([...data].reverse());
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const chartData = scans.map((s) => ({
    date: s.ScanDate?.slice(0, 10),
    savings: s.total_potential_monthly_savings,
    findings: s.total_findings,
  }));

  return (
    <div>
      <div className="toolbar">
        <h2>History</h2>
      </div>

      {error && <div className="error-banner">Couldn't reach the API ({error}).</div>}

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Monthly Savings Trend</h3>
        {chartData.length ? (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262f45" />
              <XAxis dataKey="date" stroke="#8b93a7" fontSize={12} />
              <YAxis stroke="#8b93a7" fontSize={12} />
              <Tooltip contentStyle={{ background: "#171d2c", border: "1px solid #262f45" }} />
              <Line type="monotone" dataKey="savings" stroke="#4f8cff" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state">{loading ? "Loading…" : "No scan history yet."}</div>
        )}
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Scan Log</h3>
        {scans.length ? (
          <table>
            <thead>
              <tr>
                <th>Scan ID</th>
                <th>Date</th>
                <th>Findings</th>
                <th>Potential Savings</th>
              </tr>
            </thead>
            <tbody>
              {[...scans].reverse().map((s) => (
                <tr key={s.ScanID}>
                  <td>{s.ScanID}</td>
                  <td>{s.ScanDate?.slice(0, 19).replace("T", " ")}</td>
                  <td>{s.total_findings}</td>
                  <td>${s.total_potential_monthly_savings}/mo</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">{loading ? "Loading…" : "No scans recorded yet."}</div>
        )}
      </div>
    </div>
  );
}

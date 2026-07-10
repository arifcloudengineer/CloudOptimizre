import React, { useState } from "react";
import { api } from "../api/client.js";

export default function ScanButton({ onTriggered }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  async function handleClick() {
    setLoading(true);
    setMessage(null);
    try {
      await api.triggerScan();
      setMessage("Scan triggered — results will appear after the Lambda finishes (usually under a minute).");
      onTriggered?.();
    } catch (e) {
      setMessage(`Failed to trigger scan: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button className="primary" onClick={handleClick} disabled={loading}>
        {loading ? "Triggering…" : "Run Scan Now"}
      </button>
      {message && <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 8 }}>{message}</div>}
    </div>
  );
}

import React from "react";

export default function StatCard({ label, value, variant }) {
  return (
    <div className={`card ${variant || ""}`}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}

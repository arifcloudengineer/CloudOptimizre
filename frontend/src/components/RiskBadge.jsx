import React from "react";

export default function RiskBadge({ risk }) {
  const level = (risk || "low").toLowerCase();
  return <span className={`risk-badge risk-${level}`}>{level}</span>;
}

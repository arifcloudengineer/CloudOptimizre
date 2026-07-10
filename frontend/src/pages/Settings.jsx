import React from "react";

export default function Settings() {
  return (
    <div>
      <div className="toolbar">
        <h2>Settings</h2>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Scan Configuration</h3>
        <p style={{ color: "var(--text-dim)", fontSize: 13, lineHeight: 1.6 }}>
          These values are set via Terraform variables at deploy time, not from this
          dashboard, so a bad UI setting can never accidentally change what runs
          against your AWS account. To change them, edit{" "}
          <code>terraform/environments/dev/terraform.tfvars</code> and re-run{" "}
          <code>terraform apply</code>.
        </p>
        <table>
          <tbody>
            <tr><td>Scan schedule</td><td><code>var.scan_schedule</code> (default: <code>rate(1 day)</code>)</td></tr>
            <tr><td>Alert email</td><td><code>var.alert_email</code></td></tr>
            <tr><td>Savings alert threshold</td><td><code>SAVINGS_ALERT_LIMIT</code> env var on the Lambda (default: $50/mo)</td></tr>
            <tr><td>Auto-remediation allow-list</td><td><code>SAFE_ACTIONS</code> in <code>backend/api/main.py</code> (release, tag, delete-snapshot)</td></tr>
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>About</h3>
        <p style={{ color: "var(--text-dim)", fontSize: 13, lineHeight: 1.6 }}>
          CloudOptimizer — AWS FinOps &amp; Cost Optimization Platform.
          See the root <code>README.md</code> for architecture, deployment, and API docs.
        </p>
      </div>
    </div>
  );
}

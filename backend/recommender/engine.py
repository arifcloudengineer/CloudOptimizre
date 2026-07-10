"""
Recommendation engine.

Takes raw Finding objects from the scanners and turns them into actionable
recommendations with a risk rating and confidence, so the API/dashboard
never has to embed scanner-specific logic.
"""

# reason_code -> (recommendation, risk, action)
RULES = {
    "EC2:Stopped": ("Terminate instance if no longer needed, or snapshot + terminate to stop EBS billing", "medium", "terminate"),
    "EC2:Idle": ("Downsize instance type or schedule stop/start outside business hours", "low", "downsize"),
    "EC2:MissingTags": ("Tag resource for cost allocation and ownership tracking", "low", "tag"),
    "EC2:OldAMI": ("Deregister AMI and delete backing snapshots if no longer needed for rollback", "medium", "deregister"),
    "EBS:Unattached": ("Snapshot for safety, then delete the volume", "low", "delete"),
    "EBS:LargeVolume": ("Review actual usage; resize down if over-provisioned", "medium", "resize"),
    "EBS:StaleSnapshot": ("Delete snapshot if no longer required for recovery", "low", "delete"),
    "EIP:Unattached": ("Release the Elastic IP if not needed", "low", "release"),
    "RDS:Idle": ("Stop or terminate the database instance; consider Aurora Serverless for bursty workloads", "high", "review"),
    "RDS:Oversized": ("Right-size to a smaller instance class based on CloudWatch metrics", "medium", "downsize"),
    "S3:NoLifecyclePolicy": ("Add a lifecycle policy to transition/expire old objects", "low", "configure"),
    "S3:VersioningNoExpiry": ("Add noncurrent version expiration rule to versioning config", "low", "configure"),
    "S3:PublicBucket": ("Restrict bucket policy / enable Block Public Access immediately", "critical", "secure"),
    "ELB:Unused": ("Delete load balancer if no active targets are expected", "medium", "delete"),
    "NAT:Idle": ("Delete NAT Gateway or replace with a NAT instance / VPC endpoint if traffic is minimal", "medium", "delete"),
}

RISK_WEIGHT = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def generate_recommendations(findings):
    """findings: list[Finding] -> list[dict] recommendation objects."""
    recommendations = []
    for f in findings:
        rule = RULES.get(f.resource_type)
        if not rule:
            continue
        recommendation, risk, action = rule
        recommendations.append({
            "ResourceID": f.resource_id,
            "ResourceType": f.resource_type,
            "Region": f.region,
            "Condition": f.reason,
            "Recommendation": recommendation,
            "Action": action,
            "Risk": risk,
            "EstimatedMonthlySavings": f.monthly_cost,
            "Tags": f.tags,
            "Metadata": f.metadata,
        })

    recommendations.sort(key=lambda r: (-r["EstimatedMonthlySavings"], -RISK_WEIGHT[r["Risk"]]))
    return recommendations


def summarize(recommendations):
    total_savings = round(sum(r["EstimatedMonthlySavings"] for r in recommendations), 2)
    by_risk = {}
    for r in recommendations:
        by_risk[r["Risk"]] = by_risk.get(r["Risk"], 0) + 1
    return {
        "total_findings": len(recommendations),
        "total_potential_monthly_savings": total_savings,
        "findings_by_risk": by_risk,
    }

# CloudOptimizer — Project Requirements

## Problem Statement
Companies routinely overspend on AWS because unused, idle, or oversized resources
accumulate silently: stopped EC2 instances still billing for attached EBS, orphaned
Elastic IPs, unattached volumes, forgotten snapshots, oversized RDS instances, and
S3 buckets with no lifecycle policy. CloudOptimizer scans an AWS account, quantifies
the waste, recommends fixes with an estimated dollar impact and risk level, and can
optionally execute the safe, reversible fixes automatically.

## MVP Questions Answered
| Question | How CloudOptimizer answers it |
|---|---|
| How much am I spending? | Cost Explorer pull + resource inventory, surfaced on the dashboard |
| Which resources are wasting money? | Rule-based scanner across EC2, EBS, EIP, S3, RDS |
| How much can I save? | Static pricing engine converts each finding into $/month |
| What should I do? | Recommendation engine maps finding → action + risk tier |
| Can I automate simple savings? | `/optimize` endpoint executes low-risk actions (e.g. release unattached EIP) behind an explicit confirmation flag |

## In Scope (v1)
- EC2: stopped >30 days, low CPU (<5% over 14d via CloudWatch), missing required tags, old AMIs (>180 days)
- EBS: unattached volumes, large volumes (>=500GB), old/orphaned snapshots (>90 days)
- Elastic IP: unattached
- S3: missing lifecycle rule, versioning without expiry rule, public bucket flag
- RDS: idle (near-zero connections over 14d), oversized instance classes
- Load Balancer: no target groups / no healthy targets
- NAT Gateway: near-zero traffic over 14d

## Out of Scope (v1)
- Multi-account / AWS Organizations support
- Reserved Instance / Savings Plan recommendations
- Auto-remediation of anything above "low risk" (e.g. no automatic instance termination)

## Non-Functional Requirements
- Least-privilege IAM (no `AdministratorAccess`)
- Scans must be idempotent and safe to re-run
- All destructive actions require `dry_run=false` explicitly passed by the caller
- Infra fully defined in Terraform, one `terraform apply` provisions everything

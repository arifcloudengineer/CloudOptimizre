# CloudOptimizer — AWS FinOps & Cost Optimization Platform

CloudOptimizer scans an AWS account for wasted spend — stopped instances still
billing for EBS, unattached volumes and Elastic IPs, idle RDS databases,
unlifecycled S3 buckets, unused load balancers, idle NAT Gateways — and turns
each finding into a dollar estimate, a risk-rated recommendation, and
(optionally) a one-click safe fix.

## Problem Statement

Companies routinely overspend on AWS because unused, idle, or oversized
resources accumulate silently. CloudOptimizer scans an account, quantifies the
waste, recommends fixes with an estimated dollar impact and risk level, and
can optionally execute the safe, reversible fixes automatically.

## Architecture

```
EventBridge (daily) ──or── POST /scan
        │
        ▼
Lambda (lambda_handler.py) ──► Scanners (EC2/EBS/EIP/RDS/S3/ELB/NAT via boto3)
        │
        ▼
Recommendation Engine (pure Python) ──► Pricing Engine (static $/mo table)
        │
        ▼
DynamoDB (resources + scan-history) ──► SNS (email alerts)
        │
        ▼
FastAPI (backend/api) ──► React Dashboard (frontend)
```

Full write-up, sequence diagram, and data model: [`docs/Architecture.md`](docs/Architecture.md).
Editable diagram: [`architecture/cloudoptimizer.drawio`](architecture/cloudoptimizer.drawio) (open at [app.diagrams.net](https://app.diagrams.net)).

## Features

- **7 resource scanners**: EC2 (stopped, idle, missing tags, old AMIs), EBS
  (unattached, oversized, stale snapshots), Elastic IP (unattached), RDS
  (idle, oversized), S3 (no lifecycle policy, versioning without expiry,
  public bucket), ELB (no healthy targets), NAT Gateway (near-zero traffic).
- **Recommendation engine** — maps every finding to a recommended action, a
  risk tier (`low`/`medium`/`high`/`critical`), and an estimated $/month.
- **Static pricing engine** — converts resource attributes into a cost
  estimate without depending on the (slow, region-locked) AWS Price List API.
- **REST API** (FastAPI) — `/dashboard`, `/recommendations`, `/resources`,
  `/cost-summary`, `/history`, `POST /scan`, `POST /optimize`.
- **Guarded auto-remediation** — `POST /optimize` only executes a small,
  explicit allow-list of safe/reversible actions (release an EIP, tag a
  resource, delete an unattached EBS volume/snapshot) and defaults to
  `dry_run=true`.
- **React dashboard** — Dashboard, Resources, Recommendations, Savings,
  History, Settings, with charts (Recharts) and a "Run Scan Now" button.
- **Notifications** — one consolidated SNS/email alert per scan when any
  finding exceeds a savings threshold or is `critical` risk.
- **Infra as code** — Terraform modules for IAM, Lambda, DynamoDB,
  EventBridge, SNS, S3; `terraform apply` provisions everything.
- **CI/CD** — GitHub Actions: Terraform validate, pytest, frontend build,
  and a gated `main`-branch deploy job.
- **Tests** — 25 pytest tests covering the pricing engine, recommendation
  engine, all scanners (via `moto`-mocked AWS), and the API (via a mocked
  DynamoDB + FastAPI `TestClient`). No AWS account needed to run them.

## Technologies

Python 3.12 · boto3 · FastAPI · Pydantic · Mangum · pytest · moto ·
Terraform · AWS (Lambda, DynamoDB, EventBridge, SNS, S3, IAM) ·
React 18 · Vite · Recharts · React Router

## Folder Structure

```
CloudOptimizer/
├── architecture/
│   └── cloudoptimizer.drawio
├── backend/
│   ├── api/              # FastAPI app + Mangum Lambda wrapper
│   ├── scanner/           # ec2, ebs, eip, rds, s3, elb, nat + shared base.py
│   ├── recommender/       # finding -> recommendation + risk mapping
│   ├── pricing/           # static price table + pricing_engine.py
│   ├── notifier/          # SNS alerting
│   ├── models/             # Pydantic schemas
│   └── lambda_handler.py  # scanner Lambda entry point
├── frontend/               # React + Vite dashboard
├── terraform/
│   ├── modules/            # iam, lambda, dynamodb, eventbridge, sns, s3
│   └── environments/dev/   # root module wiring it all together
├── .github/workflows/ci-cd.yml
├── docs/                   # ProjectRequirements, Architecture, Roadmap, scanner-checklist
├── reports/                 # scan report exports land here (gitignored, kept via .gitkeep)
├── scripts/                # deploy.sh, destroy.sh, run_api_local.sh
└── tests/                   # pytest — pricing, recommender, scanners, API
```

## Getting Started

### 1. Run the tests (no AWS account needed)

```bash
cd CloudOptimizer
pip install -r backend/requirements.txt
PYTHONPATH=backend:tests pytest tests/ -v
```

All scanner and API tests run against `moto`-mocked AWS services, so this
works with zero real AWS credentials.

### 2. Run the backend + a scan locally against your own AWS account

```bash
# One-time: configure AWS credentials with read access to EC2/EBS/RDS/S3/ELB/NAT/CloudWatch
aws configure   # or export AWS_PROFILE=your-profile

# Dry-run the scanner locally (prints findings, does not write to DynamoDB/SNS)
cd backend
python lambda_handler.py

# Run the API (reads from DynamoDB, so deploy Terraform first — see step 3 —
# or point RESOURCES_TABLE/SCAN_HISTORY_TABLE at existing tables)
../scripts/run_api_local.sh
# API docs: http://localhost:8000/docs
```

### 3. Deploy the infrastructure

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars: your alert email, region, schedule

# One-time: create the S3 bucket + DynamoDB table for Terraform remote state,
# matching the backend block in main.tf, OR remove the backend "s3" block to
# use local state for a quick test.

cd ../../..
./scripts/deploy.sh dev
```

This provisions: DynamoDB (findings + scan-history), the scanner Lambda,
its least-privilege IAM role, an EventBridge daily schedule, an SNS topic
(with an email subscription if you set `alert_email`), and an S3 bucket for
report exports.

The FastAPI app can run anywhere that can reach those DynamoDB tables — as a
second Lambda behind an API Gateway/Function URL (`backend/api/lambda_handler.py`
is ready for this), on ECS/Fargate, or on a small EC2 instance. Terraform for
the API layer is intentionally left for you to add in whichever shape fits
your portfolio story (this build focuses the IaC on the always-on scanning
pipeline).

### 4. Run the frontend

```bash
cd frontend
cp .env.example .env      # point VITE_API_BASE_URL at your running API
npm install
npm run dev                # http://localhost:5173
```

### 5. Tear down

```bash
./scripts/destroy.sh dev
```

## API Reference

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/dashboard` | Card-level summary: open findings, savings, score, critical count |
| GET | `/recommendations` | Filterable list (`risk`, `resource_type`, `status`) |
| GET | `/resources` | All scanned resources, optionally filtered by type |
| GET | `/cost-summary` | Same shape as `/dashboard`, typed response model |
| GET | `/history?limit=30` | Recent scan summaries, for the trend chart |
| POST | `/scan` | Asynchronously invokes the scanner Lambda |
| POST | `/optimize` | Executes (or dry-runs) a remediation: `{resource_id, action, dry_run}` |

Full interactive docs at `/docs` (Swagger UI) once the API is running.

## Security Notes

- The scanner Lambda's IAM role grants only `Describe*`/`Get*`/`List*`
  read permissions plus scoped `dynamodb:*` and `sns:Publish` — never
  `AdministratorAccess` or `PowerUserAccess` (see `terraform/modules/iam`).
- `POST /optimize` only executes actions in an explicit allow-list
  (`release`, `tag`, `delete` for unattached EBS/snapshots) and defaults to
  `dry_run=true`. Anything higher-risk (terminate an instance, delete an RDS
  database) must be done manually, by design.
- A separate, narrower "remediation" IAM policy (also in `modules/iam`) is
  scoped to resources tagged `CloudOptimizerApproved=true` — attach it only
  if you want to enable automated remediation beyond the API's dry-run mode.

## Future Enhancements

- Wire up the live AWS Cost Explorer API for actual total spend (this build
  estimates *waste*, not the full bill).
- Swap the static pricing table for the live AWS Price List API for exact
  (not just directional) savings estimates.
- Multi-account support via AWS Organizations + cross-account IAM roles.
- Reserved Instance / Savings Plan coverage recommendations.
- Slack/Teams webhook notifications alongside SNS/email.

## Documentation

- [`docs/ProjectRequirements.md`](docs/ProjectRequirements.md) — problem statement, MVP scope, in/out of scope, NFRs
- [`docs/Architecture.md`](docs/Architecture.md) — component design, sequence diagram, data model
- [`docs/Roadmap.md`](docs/Roadmap.md) — phase-by-phase build status
- [`docs/scanner-checklist.md`](docs/scanner-checklist.md) — every detection rule, per resource type
- [`docs/EC2-DEPLOY.md`](docs/EC2-DEPLOY.md) — alternative deploy: single EC2 instance instead of Lambda

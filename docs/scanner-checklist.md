# Scanner Checklist

## EC2 (`backend/scanner/ec2_scanner.py`)
- [x] Stopped ≥30 days → recommend terminate (still bills attached EBS)
- [x] Low CPU <5% avg over 14d (CloudWatch) on a running instance → recommend downsize/schedule
- [x] Missing required tags (`Owner`, `Environment`) → recommend tag (no cost impact, compliance only)
- [x] Old AMI (≥180 days old, owned by account) → recommend deregister + delete backing snapshots

## EBS (`backend/scanner/ebs_scanner.py`)
- [x] Unattached volume (state = `available`) → recommend snapshot then delete
- [x] Large volume (≥500GB) → recommend review/resize regardless of attach state
- [x] Stale snapshot (source volume gone, or ≥90 days old) → recommend delete

## Elastic IP (`backend/scanner/eip_scanner.py`)
- [x] Unattached (no instance or ENI association) → recommend release
  (this is the "safe to automate" example wired to `POST /optimize`)

## RDS (`backend/scanner/rds_scanner.py`)
- [x] Idle: avg `DatabaseConnections` ≤1 over 14d → recommend stop/review
- [x] Oversized: instance class in the large-class allowlist (e.g. `db.r5.2xlarge`+) → recommend downsize

## S3 (`backend/scanner/s3_scanner.py`)
- [x] No lifecycle configuration → recommend adding one
- [x] Versioning enabled with no noncurrent-version expiration rule → recommend adding one
- [x] Bucket policy status reports public → CRITICAL alert (security, not just cost)

## Load Balancer (`backend/scanner/elb_scanner.py`)
- [x] No target groups, or no healthy registered targets → recommend delete

## NAT Gateway (`backend/scanner/nat_scanner.py`)
- [x] `BytesOutToDestination` near-zero (<1MB total) over 14d → recommend delete
  NAT Gateways are billed hourly regardless of traffic, making idle ones one of
  the highest per-hour waste items in most accounts.

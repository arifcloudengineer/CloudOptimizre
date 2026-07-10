"""
CloudOptimizer REST API
------------------------
Thin read/write layer over DynamoDB. Never talks to EC2/RDS/S3 resource APIs
directly (that's the scanner Lambda's job) -- the only two exceptions are:
  - POST /scan, which invokes the scanner Lambda asynchronously
  - POST /optimize, which executes a single, explicitly-approved, low-risk
    remediation action (e.g. release an Elastic IP)

Run locally:
    uvicorn api.main:app --reload --port 8000

Deploy: this app is wrapped by Mangum (see api/lambda_handler.py) so it can
run as a Lambda behind API Gateway/Function URL, or run standalone via
uvicorn/gunicorn on ECS/EC2 -- same code, either target.
"""
import os
import json
import time
from decimal import Decimal
from typing import Optional

import boto3
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from boto3.dynamodb.conditions import Key

from models.schemas import OptimizeRequest, OptimizeResponse, CostSummary

RESOURCES_TABLE = os.environ.get("RESOURCES_TABLE", "cloudoptimizer-resources-dev")
SCAN_HISTORY_TABLE = os.environ.get("SCAN_HISTORY_TABLE", "cloudoptimizer-resources-dev-scan-history")
SCANNER_LAMBDA_NAME = os.environ.get("SCANNER_LAMBDA_NAME", "")

app = FastAPI(title="CloudOptimizer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your dashboard's origin before production use
    allow_methods=["*"],
    allow_headers=["*"],
)

_dynamodb = None
_lambda_client = None


def dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb


def lambda_client():
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client("lambda")
    return _lambda_client


def _clean(obj):
    """DynamoDB returns Decimal -- convert to int/float for JSON responses."""
    if isinstance(obj, list):
        return [_clean(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/dashboard")
def dashboard():
    """Card-level summary: monthly spend estimate, savings, score, critical count."""
    table = dynamodb().Table(RESOURCES_TABLE)
    items = table.scan().get("Items", [])
    open_items = [i for i in items if i.get("Status", "open") == "open"]

    total_savings = sum(float(i.get("EstimatedMonthlySavings", 0)) for i in open_items)
    critical = [i for i in open_items if i.get("Risk") == "critical"]

    # Optimization score: 100 minus a penalty per open finding, floor at 0.
    # Weighted so critical findings hurt the score more than low-risk ones.
    weight = {"low": 1, "medium": 2, "high": 3, "critical": 5}
    penalty = sum(weight.get(i.get("Risk", "low"), 1) for i in open_items)
    score = max(0, 100 - penalty)

    return _clean({
        "total_open_findings": len(open_items),
        "total_potential_monthly_savings": round(total_savings, 2),
        "optimization_score": score,
        "critical_findings": len(critical),
    })


@app.get("/recommendations")
def recommendations(
    risk: Optional[str] = Query(None, description="Filter by risk: low|medium|high|critical"),
    resource_type: Optional[str] = Query(None),
    status: Optional[str] = Query("open"),
):
    table = dynamodb().Table(RESOURCES_TABLE)
    items = table.scan().get("Items", [])
    if status:
        items = [i for i in items if i.get("Status", "open") == status]
    if risk:
        items = [i for i in items if i.get("Risk") == risk]
    if resource_type:
        items = [i for i in items if i.get("ResourceType", "").startswith(resource_type)]
    items.sort(key=lambda i: -float(i.get("EstimatedMonthlySavings", 0)))
    return _clean(items)


@app.get("/resources")
def resources(resource_type: Optional[str] = Query(None)):
    """All scanned resources (open + resolved), optionally filtered by type."""
    table = dynamodb().Table(RESOURCES_TABLE)
    items = table.scan().get("Items", [])
    if resource_type:
        items = [i for i in items if i.get("ResourceType", "").startswith(resource_type)]
    return _clean(items)


@app.get("/cost-summary", response_model=CostSummary)
def cost_summary():
    table = dynamodb().Table(RESOURCES_TABLE)
    items = table.scan().get("Items", [])
    open_items = [i for i in items if i.get("Status", "open") == "open"]
    total_savings = round(sum(float(i.get("EstimatedMonthlySavings", 0)) for i in open_items), 2)
    critical = len([i for i in open_items if i.get("Risk") == "critical"])
    weight = {"low": 1, "medium": 2, "high": 3, "critical": 5}
    penalty = sum(weight.get(i.get("Risk", "low"), 1) for i in open_items)
    score = max(0, 100 - penalty)

    return CostSummary(
        total_monthly_spend_estimate=0.0,  # wire up Cost Explorer if you want real spend, not just waste
        total_potential_savings=total_savings,
        optimization_score=score,
        critical_findings=critical,
    )


@app.get("/history")
def history(limit: int = 30):
    table = dynamodb().Table(SCAN_HISTORY_TABLE)
    items = table.scan().get("Items", [])
    items.sort(key=lambda i: i.get("ScanDate", ""), reverse=True)
    return _clean(items[:limit])


@app.post("/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    """
    Triggers a scan. Two modes, chosen by whether SCANNER_LAMBDA_NAME is set:
      - Serverless deploy: invokes the scanner Lambda asynchronously.
      - EC2 / non-Lambda deploy: runs the scan in-process on a background
        thread via FastAPI's BackgroundTasks, so the request still returns
        immediately without needing a separate compute target.
    """
    if SCANNER_LAMBDA_NAME:
        try:
            lambda_client().invoke(
                FunctionName=SCANNER_LAMBDA_NAME,
                InvocationType="Event",  # async -- don't block the API on a 5min scan
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to invoke scanner Lambda: {e}")
        return {"status": "scan_triggered", "mode": "lambda", "function": SCANNER_LAMBDA_NAME}

    background_tasks.add_task(_run_scan_in_process)
    return {"status": "scan_triggered", "mode": "in_process"}


def _run_scan_in_process():
    """Runs the same scan the Lambda would, without touching AWS Lambda itself.
    Used for EC2/ECS/local deployments that have no Lambda to invoke."""
    from lambda_handler import run_full_scan, persist_results
    from recommender.engine import generate_recommendations
    from notifier.notifier import send_alerts
    import uuid
    from datetime import datetime, timezone

    scan_id = str(uuid.uuid4())
    scan_date = datetime.now(timezone.utc).isoformat()
    findings = run_full_scan()
    recommendations = generate_recommendations(findings)
    persist_results(recommendations, scan_id, scan_date)
    sns_topic_arn = os.environ.get("SNS_TOPIC_ARN", "")
    savings_limit = float(os.environ.get("SAVINGS_ALERT_LIMIT", "50"))
    send_alerts(recommendations, sns_topic_arn, savings_limit)


# Actions considered safe enough to execute from the API with dry_run=false.
# Anything not in this set (terminate, delete RDS, etc.) must be done manually
# -- this is a deliberate ceiling, not an oversight.
SAFE_ACTIONS = {"release", "tag", "delete"}  # 'delete' only for EBS snapshots / unattached volumes


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
    if req.action not in SAFE_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Action '{req.action}' is not in the auto-remediation allow-list {SAFE_ACTIONS}. "
                   f"High-risk actions must be performed manually.",
        )

    if req.dry_run:
        return OptimizeResponse(
            resource_id=req.resource_id,
            action=req.action,
            dry_run=True,
            status="simulated",
            detail=f"Dry run only -- no AWS API call made. Would have executed '{req.action}' on {req.resource_id}.",
        )

    ec2 = boto3.client("ec2")
    try:
        if req.action == "release":
            ec2.release_address(AllocationId=req.resource_id)
        elif req.action == "delete":
            ec2.delete_volume(VolumeId=req.resource_id)
        elif req.action == "tag":
            ec2.create_tags(Resources=[req.resource_id], Tags=[{"Key": "Environment", "Value": "unassigned"}])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AWS API call failed: {e}")

    # Mark resolved in DynamoDB
    table = dynamodb().Table(RESOURCES_TABLE)
    resp = table.query(KeyConditionExpression=Key("ResourceID").eq(req.resource_id))
    for item in resp.get("Items", []):
        table.update_item(
            Key={"ResourceID": item["ResourceID"], "ScanDate": item["ScanDate"]},
            UpdateExpression="SET #s = :resolved",
            ExpressionAttributeNames={"#s": "Status"},
            ExpressionAttributeValues={":resolved": "resolved"},
        )

    return OptimizeResponse(
        resource_id=req.resource_id,
        action=req.action,
        dry_run=False,
        status="executed",
        detail=f"Executed '{req.action}' on {req.resource_id} and marked resolved.",
    )

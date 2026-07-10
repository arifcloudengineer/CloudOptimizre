"""
API tests. Spins up mocked DynamoDB tables via moto, seeds them with sample
findings, and exercises the FastAPI app through TestClient -- no real AWS
account, no running server required.
"""
import os
import boto3
import pytest
from moto import mock_aws
from fastapi.testclient import TestClient

os.environ["RESOURCES_TABLE"] = "cloudoptimizer-resources-test"
os.environ["SCAN_HISTORY_TABLE"] = "cloudoptimizer-resources-test-scan-history"


@pytest.fixture
def client():
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="ap-south-1")
        resources_table = ddb.create_table(
            TableName=os.environ["RESOURCES_TABLE"],
            KeySchema=[
                {"AttributeName": "ResourceID", "KeyType": "HASH"},
                {"AttributeName": "ScanDate", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "ResourceID", "AttributeType": "S"},
                {"AttributeName": "ScanDate", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        history_table = ddb.create_table(
            TableName=os.environ["SCAN_HISTORY_TABLE"],
            KeySchema=[{"AttributeName": "ScanID", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "ScanID", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        resources_table.put_item(Item={
            "ResourceID": "i-abc123", "ScanDate": "2026-07-01T00:00:00",
            "ResourceType": "EC2:Idle", "Region": "ap-south-1", "Risk": "low",
            "EstimatedMonthlySavings": 15, "Status": "open",
            "Condition": "low cpu", "Recommendation": "downsize", "Action": "downsize",
            "Tags": {}, "Metadata": {},
        })
        resources_table.put_item(Item={
            "ResourceID": "bucket-public", "ScanDate": "2026-07-01T00:00:00",
            "ResourceType": "S3:PublicBucket", "Region": "global", "Risk": "critical",
            "EstimatedMonthlySavings": 0, "Status": "open",
            "Condition": "public bucket policy", "Recommendation": "secure it",
            "Action": "secure", "Tags": {}, "Metadata": {},
        })

        from api.main import app
        yield TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_dashboard_summary(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_open_findings"] == 2
    assert body["critical_findings"] == 1
    assert body["total_potential_monthly_savings"] == 15


def test_recommendations_filter_by_risk(client):
    resp = client.get("/recommendations", params={"risk": "critical"})
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["ResourceType"] == "S3:PublicBucket"


def test_optimize_dry_run_does_not_call_aws(client):
    resp = client.post("/optimize", json={
        "resource_id": "i-abc123", "action": "tag", "dry_run": True,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["status"] == "simulated"


def test_optimize_rejects_high_risk_action(client):
    resp = client.post("/optimize", json={
        "resource_id": "i-abc123", "action": "terminate", "dry_run": True,
    })
    assert resp.status_code == 400


def test_scan_defaults_to_in_process_mode_without_lambda_configured(client, monkeypatch):
    """On EC2 (no SCANNER_LAMBDA_NAME set) POST /scan must not try to call
    the AWS Lambda API -- it should schedule the scan as a background task
    instead and return immediately."""
    from api import main
    monkeypatch.setattr(main, "SCANNER_LAMBDA_NAME", "")
    resp = client.post("/scan")
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "in_process"

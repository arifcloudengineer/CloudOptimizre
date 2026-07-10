"""
Entry point for the CloudOptimizer scanner Lambda.
Triggered by EventBridge on a schedule (default: daily).
"""
import os
import uuid
import json
from datetime import datetime, timezone

import boto3

from scanner.ec2_scanner import scan_ec2
from scanner.ebs_scanner import scan_ebs
from scanner.eip_scanner import scan_eip
from scanner.rds_scanner import scan_rds
from scanner.s3_scanner import scan_s3
from scanner.elb_scanner import scan_elb
from scanner.nat_scanner import scan_nat
from recommender.engine import generate_recommendations, summarize
from notifier.notifier import send_alerts

RESOURCES_TABLE = os.environ.get("RESOURCES_TABLE", "cloudoptimizer-resources")
SCAN_HISTORY_TABLE = os.environ.get("SCAN_HISTORY_TABLE", "cloudoptimizer-resources-scan-history")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
SAVINGS_ALERT_LIMIT = float(os.environ.get("SAVINGS_ALERT_LIMIT", "50"))

dynamodb = boto3.resource("dynamodb")


def run_full_scan():
    """Runs every scanner and returns the combined list of findings."""
    findings = []
    findings += scan_ec2()
    findings += scan_ebs()
    findings += scan_eip()
    findings += scan_rds()
    findings += scan_s3()
    findings += scan_elb()
    findings += scan_nat()
    return findings


def persist_results(recommendations, scan_id, scan_date):
    resources_table = dynamodb.Table(RESOURCES_TABLE)
    history_table = dynamodb.Table(SCAN_HISTORY_TABLE)

    with resources_table.batch_writer() as batch:
        for r in recommendations:
            item = dict(r)
            item["ScanDate"] = scan_date
            item["Status"] = "open"
            batch.put_item(Item=_stringify_floats(item))

    summary = summarize(recommendations)
    history_table.put_item(Item=_stringify_floats({
        "ScanID": scan_id,
        "ScanDate": scan_date,
        **summary,
    }))
    return summary


def _stringify_floats(obj):
    """DynamoDB requires Decimal, not float — convert recursively via JSON round-trip."""
    from decimal import Decimal
    return json.loads(json.dumps(obj), parse_float=Decimal)


def handler(event, context):
    scan_id = str(uuid.uuid4())
    scan_date = datetime.now(timezone.utc).isoformat()

    findings = run_full_scan()
    recommendations = generate_recommendations(findings)
    summary = persist_results(recommendations, scan_id, scan_date)
    send_alerts(recommendations, SNS_TOPIC_ARN, SAVINGS_ALERT_LIMIT)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "scan_id": scan_id,
            "scan_date": scan_date,
            **summary,
        }),
    }


if __name__ == "__main__":
    # Local dry run: prints findings without touching DynamoDB/SNS.
    findings = run_full_scan()
    recs = generate_recommendations(findings)
    print(json.dumps(recs, indent=2, default=str))
    print(json.dumps(summarize(recs), indent=2))

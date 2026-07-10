"""RDS scanner — idle databases (low connections) and oversized instance classes."""
from datetime import datetime, timedelta, timezone
from .base import get_client, Finding
from pricing.pricing_engine import estimate_rds_monthly_cost

IDLE_CONNECTION_THRESHOLD = 1
OVERSIZED_CLASSES = {"db.r5.2xlarge", "db.r5.4xlarge", "db.m5.2xlarge", "db.m5.4xlarge"}


def _avg_connections(cw, db_id, days=14):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    resp = cw.get_metric_statistics(
        Namespace="AWS/RDS",
        MetricName="DatabaseConnections",
        Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_id}],
        StartTime=start,
        EndTime=end,
        Period=86400,
        Statistics=["Average"],
    )
    points = resp.get("Datapoints", [])
    if not points:
        return None
    return round(sum(p["Average"] for p in points) / len(points), 2)


def scan_rds(region=None):
    rds = get_client("rds", region)
    cw = get_client("cloudwatch", region)
    findings = []

    instances = rds.describe_db_instances()["DBInstances"]
    for db in instances:
        db_id = db["DBInstanceIdentifier"]
        db_class = db["DBInstanceClass"]
        monthly_cost = estimate_rds_monthly_cost(db_class)
        tags = {}
        try:
            tag_resp = rds.list_tags_for_resource(ResourceName=db["DBInstanceArn"])
            tags = {t["Key"]: t["Value"] for t in tag_resp.get("TagList", [])}
        except Exception:
            pass

        avg_conn = _avg_connections(cw, db_id)
        if avg_conn is not None and avg_conn <= IDLE_CONNECTION_THRESHOLD:
            findings.append(Finding(
                db_id, "RDS:Idle", region or "default",
                f"Average of {avg_conn} connections over last 14 days — likely idle",
                monthly_cost=monthly_cost,
                tags=tags,
                metadata={"db_class": db_class, "avg_connections": avg_conn},
            ))

        if db_class in OVERSIZED_CLASSES:
            findings.append(Finding(
                db_id, "RDS:Oversized", region or "default",
                f"Instance class {db_class} is large — verify actual load requires this size",
                monthly_cost=monthly_cost * 0.4,
                tags=tags,
                metadata={"db_class": db_class},
            ))

    return findings

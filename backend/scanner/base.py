"""Shared helpers for all resource scanners."""
import boto3
from datetime import datetime, timedelta, timezone


def get_client(service, region=None):
    return boto3.client(service, region_name=region) if region else boto3.client(service)


def get_avg_cpu_utilization(instance_id, region=None, days=14):
    """Return average CPU utilization % for an EC2 instance over the last N days."""
    cw = get_client("cloudwatch", region)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    resp = cw.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start,
        EndTime=end,
        Period=86400,
        Statistics=["Average"],
    )
    points = resp.get("Datapoints", [])
    if not points:
        return None
    return round(sum(p["Average"] for p in points) / len(points), 2)


def days_since(timestamp):
    if timestamp is None:
        return None
    now = datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return (now - timestamp).days


class Finding:
    """A single scan finding, normalized across all scanners."""

    def __init__(self, resource_id, resource_type, region, reason,
                 monthly_cost=0.0, tags=None, metadata=None):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.region = region
        self.reason = reason
        self.monthly_cost = round(monthly_cost, 2)
        self.tags = tags or {}
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            "ResourceID": self.resource_id,
            "ResourceType": self.resource_type,
            "Region": self.region,
            "Reason": self.reason,
            "MonthlyCost": self.monthly_cost,
            "Tags": self.tags,
            "Metadata": self.metadata,
        }

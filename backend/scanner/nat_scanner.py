"""NAT Gateway scanner — gateways with near-zero traffic (idle but billed hourly)."""
from datetime import datetime, timedelta, timezone
from .base import get_client, Finding
from pricing.pricing_engine import NAT_GATEWAY_MONTHLY_COST

IDLE_BYTES_THRESHOLD = 1_000_000  # ~1MB total over the window


def scan_nat(region=None):
    ec2 = get_client("ec2", region)
    cw = get_client("cloudwatch", region)
    findings = []

    gateways = ec2.describe_nat_gateways(Filter=[{"Name": "state", "Values": ["available"]}])["NatGateways"]
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=14)

    for gw in gateways:
        nat_id = gw["NatGatewayId"]
        resp = cw.get_metric_statistics(
            Namespace="AWS/NATGateway",
            MetricName="BytesOutToDestination",
            Dimensions=[{"Name": "NatGatewayId", "Value": nat_id}],
            StartTime=start,
            EndTime=end,
            Period=86400,
            Statistics=["Sum"],
        )
        total_bytes = sum(p["Sum"] for p in resp.get("Datapoints", []))
        if total_bytes < IDLE_BYTES_THRESHOLD:
            findings.append(Finding(
                nat_id, "NAT:Idle", region or "default",
                f"Only {int(total_bytes)} bytes transferred in last 14 days — likely idle",
                monthly_cost=NAT_GATEWAY_MONTHLY_COST,
                metadata={"vpc_id": gw.get("VpcId")},
            ))

    return findings

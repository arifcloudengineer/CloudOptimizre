"""Elastic IP scanner — unattached (and therefore billed) addresses."""
from .base import get_client, Finding
from pricing.pricing_engine import ELASTIC_IP_UNATTACHED_MONTHLY_COST


def scan_eip(region=None):
    ec2 = get_client("ec2", region)
    findings = []
    addresses = ec2.describe_addresses()["Addresses"]

    for addr in addresses:
        # Use falsy checks rather than key-presence checks: some SDK/mock
        # responses include InstanceId/NetworkInterfaceId as empty strings
        # rather than omitting the key entirely for unattached addresses.
        if not addr.get("InstanceId") and not addr.get("NetworkInterfaceId"):
            tags = {t["Key"]: t["Value"] for t in addr.get("Tags", [])}
            findings.append(Finding(
                addr.get("AllocationId", addr.get("PublicIp")), "EIP:Unattached", region or "default",
                f"Elastic IP {addr.get('PublicIp')} is not associated with any resource",
                monthly_cost=ELASTIC_IP_UNATTACHED_MONTHLY_COST,
                tags=tags,
                metadata={"public_ip": addr.get("PublicIp")},
            ))
    return findings

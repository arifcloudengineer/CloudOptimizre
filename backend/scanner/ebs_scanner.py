"""EBS scanner — unattached volumes, oversized unused volumes, orphaned snapshots."""
from .base import get_client, days_since, Finding
from pricing.pricing_engine import estimate_ebs_monthly_cost

LARGE_VOLUME_GB_THRESHOLD = 500
SNAPSHOT_AGE_DAYS_THRESHOLD = 90


def scan_ebs(region=None):
    ec2 = get_client("ec2", region)
    findings = []

    volumes = ec2.describe_volumes()["Volumes"]
    for volume in volumes:
        volume_id = volume["VolumeId"]
        size_gb = volume["Size"]
        volume_type = volume.get("VolumeType", "gp2")
        tags = {t["Key"]: t["Value"] for t in volume.get("Tags", [])}
        monthly_cost = estimate_ebs_monthly_cost(size_gb, volume_type)

        if volume["State"] == "available":  # unattached
            findings.append(Finding(
                volume_id, "EBS:Unattached", region or "default",
                f"Volume ({size_gb}GB, {volume_type}) is not attached to any instance",
                monthly_cost=monthly_cost,
                tags=tags,
                metadata={"size_gb": size_gb, "volume_type": volume_type},
            ))
        elif size_gb >= LARGE_VOLUME_GB_THRESHOLD:
            findings.append(Finding(
                volume_id, "EBS:LargeVolume", region or "default",
                f"Large volume ({size_gb}GB) — verify utilization matches provisioned size",
                monthly_cost=monthly_cost,
                tags=tags,
                metadata={"size_gb": size_gb, "volume_type": volume_type},
            ))

    # Orphaned / stale snapshots (no source volume, or very old)
    snapshots = ec2.describe_snapshots(OwnerIds=["self"])["Snapshots"]
    existing_volume_ids = {v["VolumeId"] for v in volumes}
    for snap in snapshots:
        age_days = days_since(snap.get("StartTime"))
        source_missing = snap.get("VolumeId") not in existing_volume_ids
        if source_missing or (age_days and age_days >= SNAPSHOT_AGE_DAYS_THRESHOLD):
            reason = "Source volume no longer exists" if source_missing else f"Snapshot is {age_days} days old"
            findings.append(Finding(
                snap["SnapshotId"], "EBS:StaleSnapshot", region or "default",
                reason,
                monthly_cost=estimate_ebs_monthly_cost(snap.get("VolumeSize", 0), "snapshot"),
                metadata={"volume_size": snap.get("VolumeSize", 0), "age_days": age_days},
            ))

    return findings

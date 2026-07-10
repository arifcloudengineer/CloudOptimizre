"""EC2 scanner — stopped instances, idle instances, low CPU, missing tags, old AMIs."""
from datetime import datetime, timezone
from .base import get_client, get_avg_cpu_utilization, days_since, Finding
from pricing.pricing_engine import estimate_ec2_monthly_cost

REQUIRED_TAGS = ["Environment", "Owner"]
LOW_CPU_THRESHOLD = 5.0
STOPPED_DAYS_THRESHOLD = 30
OLD_AMI_DAYS_THRESHOLD = 180


def scan_ec2(region=None):
    ec2 = get_client("ec2", region)
    findings = []

    paginator = ec2.get_paginator("describe_instances")
    for page in paginator.paginate():
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                instance_id = instance["InstanceId"]
                state = instance["State"]["Name"]
                instance_type = instance.get("InstanceType", "unknown")
                tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
                monthly_cost = estimate_ec2_monthly_cost(instance_type)

                # 1. Stopped instances still incurring EBS cost
                if state == "stopped":
                    launch_time = instance.get("LaunchTime")
                    stopped_days = days_since(launch_time)
                    if stopped_days and stopped_days >= STOPPED_DAYS_THRESHOLD:
                        findings.append(Finding(
                            instance_id, "EC2:Stopped", region or "default",
                            f"Instance stopped for {stopped_days}+ days, still billed for attached EBS",
                            monthly_cost=monthly_cost * 0.1,
                            tags=tags,
                            metadata={"instance_type": instance_type, "state": state},
                        ))
                    continue

                if state != "running":
                    continue

                # 2. Idle / low CPU running instances
                avg_cpu = get_avg_cpu_utilization(instance_id, region)
                if avg_cpu is not None and avg_cpu < LOW_CPU_THRESHOLD:
                    findings.append(Finding(
                        instance_id, "EC2:Idle", region or "default",
                        f"Average CPU utilization {avg_cpu}% over last 14 days (< {LOW_CPU_THRESHOLD}%)",
                        monthly_cost=monthly_cost,
                        tags=tags,
                        metadata={"instance_type": instance_type, "avg_cpu": avg_cpu},
                    ))

                # 3. Missing required tags
                missing = [t for t in REQUIRED_TAGS if t not in tags]
                if missing:
                    findings.append(Finding(
                        instance_id, "EC2:MissingTags", region or "default",
                        f"Missing required tags: {', '.join(missing)}",
                        monthly_cost=0.0,
                        tags=tags,
                        metadata={"missing_tags": missing},
                    ))

    # 4. Old / unused AMIs owned by this account
    images = ec2.describe_images(Owners=["self"])["Images"]
    for image in images:
        creation_date = datetime.strptime(image["CreationDate"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        age_days = days_since(creation_date)
        if age_days and age_days >= OLD_AMI_DAYS_THRESHOLD:
            findings.append(Finding(
                image["ImageId"], "EC2:OldAMI", region or "default",
                f"AMI is {age_days} days old and may be unused",
                monthly_cost=0.0,
                metadata={"name": image.get("Name", ""), "age_days": age_days},
            ))

    return findings

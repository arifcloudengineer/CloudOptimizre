"""Load balancer scanner — ELBs/ALBs/NLBs with zero registered/healthy targets."""
from .base import get_client, Finding
from pricing.pricing_engine import LOAD_BALANCER_MONTHLY_COST


def scan_elb(region=None):
    elbv2 = get_client("elbv2", region)
    findings = []

    load_balancers = elbv2.describe_load_balancers()["LoadBalancers"]
    for lb in load_balancers:
        lb_arn = lb["LoadBalancerArn"]
        lb_name = lb["LoadBalancerName"]

        target_groups = elbv2.describe_target_groups(LoadBalancerArn=lb_arn)["TargetGroups"]
        has_healthy_target = False
        for tg in target_groups:
            health = elbv2.describe_target_health(TargetGroupArn=tg["TargetGroupArn"])
            healthy = [t for t in health["TargetHealthDescriptions"]
                       if t["TargetHealth"]["State"] == "healthy"]
            if healthy:
                has_healthy_target = True
                break

        if not target_groups or not has_healthy_target:
            findings.append(Finding(
                lb_name, "ELB:Unused", region or "default",
                "Load balancer has no target groups or no healthy registered targets",
                monthly_cost=LOAD_BALANCER_MONTHLY_COST,
                metadata={"type": lb.get("Type", "application")},
            ))

    return findings

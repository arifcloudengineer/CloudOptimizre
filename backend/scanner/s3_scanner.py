"""S3 scanner — missing lifecycle policies, excessive old versions, public buckets."""
from .base import get_client, Finding


def scan_s3():
    s3 = get_client("s3")
    findings = []
    buckets = s3.list_buckets()["Buckets"]

    for bucket in buckets:
        name = bucket["Name"]

        # Missing lifecycle configuration
        try:
            s3.get_bucket_lifecycle_configuration(Bucket=name)
        except s3.exceptions.ClientError as e:
            if "NoSuchLifecycleConfiguration" in str(e):
                findings.append(Finding(
                    name, "S3:NoLifecyclePolicy", "global",
                    "Bucket has no lifecycle policy — old/incomplete objects accumulate cost indefinitely",
                    monthly_cost=0.0,
                ))

        # Versioning left on with no cleanup -> old versions pile up
        try:
            versioning = s3.get_bucket_versioning(Bucket=name)
            if versioning.get("Status") == "Enabled":
                findings.append(Finding(
                    name, "S3:VersioningNoExpiry", "global",
                    "Versioning enabled without a noncurrent version expiration rule",
                    monthly_cost=0.0,
                ))
        except Exception:
            pass

        # Public bucket check (critical — security + cost via egress abuse)
        try:
            status = s3.get_bucket_policy_status(Bucket=name)
            if status.get("PolicyStatus", {}).get("IsPublic"):
                findings.append(Finding(
                    name, "S3:PublicBucket", "global",
                    "Bucket policy allows public access — critical security and cost risk",
                    monthly_cost=0.0,
                    metadata={"severity": "critical"},
                ))
        except s3.exceptions.ClientError:
            pass  # no bucket policy at all is fine

    return findings

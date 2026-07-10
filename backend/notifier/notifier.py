"""SNS notifications for high-value savings and critical security findings."""
import json
import boto3

SAVINGS_ALERT_DEFAULT_THRESHOLD = 50.0


def send_alerts(recommendations, topic_arn, savings_threshold=SAVINGS_ALERT_DEFAULT_THRESHOLD):
    """
    Sends one consolidated SNS notification if:
      - any single finding has estimated savings > threshold, or
      - any finding is marked 'critical' risk (e.g. public S3 bucket)
    Returns the message that was published (or None if nothing qualified).
    """
    if not topic_arn:
        return None

    high_value = [r for r in recommendations if r["EstimatedMonthlySavings"] > savings_threshold]
    critical = [r for r in recommendations if r["Risk"] == "critical"]

    if not high_value and not critical:
        return None

    sns = boto3.client("sns")
    lines = []
    if critical:
        lines.append(f"CRITICAL SECURITY FINDINGS ({len(critical)}):")
        for r in critical:
            lines.append(f"  - {r['ResourceType']} {r['ResourceID']}: {r['Condition']}")
    if high_value:
        total = round(sum(r["EstimatedMonthlySavings"] for r in high_value), 2)
        lines.append(f"\nHIGH-VALUE SAVINGS OPPORTUNITIES ({len(high_value)}, ${total}/mo total):")
        for r in high_value:
            lines.append(f"  - {r['ResourceType']} {r['ResourceID']}: ${r['EstimatedMonthlySavings']}/mo — {r['Recommendation']}")

    message = "\n".join(lines)
    sns.publish(
        TopicArn=topic_arn,
        Subject="CloudOptimizer: New cost/security findings",
        Message=message,
    )
    return message

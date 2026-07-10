"""
Pricing Engine
--------------
Converts a resource attribute (instance type, volume size, db class...) into
an estimated USD/month figure, using a static price table (price_table.json).

Design decision: static table instead of the live AWS Price List API.
  - Pricing API is region-locked to us-east-1 and slow/awkward to query for a
    quick per-resource lookup (it's built for billing reconciliation, not
    real-time estimates).
  - Calling out to it from every scanner invocation would add latency +
    another IAM permission + another failure mode to the Lambda's hot path.
  - A savings *estimate* only needs to be directionally right, not exact to
    the cent -- the point is "is this worth investigating", not a bill.
If you want live pricing, swap load_price_table() for a cached
boto3.client("pricing", region_name="us-east-1") lookup (cache in DynamoDB or
/tmp with a TTL, since the Pricing API is too slow to call per-resource).
"""
import json
import os

PRICE_TABLE_PATH = os.path.join(os.path.dirname(__file__), "price_table.json")
_CACHE = None


def load_price_table():
    global _CACHE
    if _CACHE is None:
        with open(PRICE_TABLE_PATH) as f:
            _CACHE = json.load(f)
    return _CACHE


def estimate_ec2_monthly_cost(instance_type):
    table = load_price_table()["EC2"]
    return table.get(instance_type, table["unknown"])


def estimate_ebs_monthly_cost(size_gb, volume_type="gp3"):
    """volume_type may also be 'snapshot' for EBS snapshot storage pricing."""
    table = load_price_table()["EBS_GB_MONTH"]
    rate = table.get(volume_type, table["gp3"])
    return round(size_gb * rate, 2)


def estimate_rds_monthly_cost(db_class):
    table = load_price_table()["RDS"]
    return table.get(db_class, table["unknown"])


ELASTIC_IP_UNATTACHED_MONTHLY_COST = load_price_table()["ELASTIC_IP_UNATTACHED_MONTHLY_COST"]
LOAD_BALANCER_MONTHLY_COST = load_price_table()["LOAD_BALANCER_MONTHLY_COST"]
NAT_GATEWAY_MONTHLY_COST = load_price_table()["NAT_GATEWAY_MONTHLY_COST"]

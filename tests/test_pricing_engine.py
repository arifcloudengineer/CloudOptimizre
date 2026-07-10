"""Tests for backend/pricing/pricing_engine.py"""
from pricing.pricing_engine import (
    estimate_ec2_monthly_cost,
    estimate_ebs_monthly_cost,
    estimate_rds_monthly_cost,
    ELASTIC_IP_UNATTACHED_MONTHLY_COST,
    LOAD_BALANCER_MONTHLY_COST,
    NAT_GATEWAY_MONTHLY_COST,
)


def test_known_ec2_instance_type_returns_positive_cost():
    cost = estimate_ec2_monthly_cost("t3.micro")
    assert cost > 0


def test_unknown_ec2_instance_type_falls_back_to_default():
    cost = estimate_ec2_monthly_cost("some.made.up.type")
    assert cost > 0  # falls back to the "unknown" bucket, never raises


def test_ebs_cost_scales_with_size():
    small = estimate_ebs_monthly_cost(10, "gp3")
    large = estimate_ebs_monthly_cost(500, "gp3")
    assert large > small
    assert large == round(500 * (large / 500), 2)


def test_ebs_snapshot_pricing_differs_from_gp3():
    gp3_cost = estimate_ebs_monthly_cost(100, "gp3")
    snap_cost = estimate_ebs_monthly_cost(100, "snapshot")
    assert gp3_cost != snap_cost


def test_rds_known_class_positive():
    assert estimate_rds_monthly_cost("db.t3.micro") > 0


def test_rds_unknown_class_falls_back():
    assert estimate_rds_monthly_cost("db.totally.fake") > 0


def test_flat_rate_constants_are_positive():
    assert ELASTIC_IP_UNATTACHED_MONTHLY_COST > 0
    assert LOAD_BALANCER_MONTHLY_COST > 0
    assert NAT_GATEWAY_MONTHLY_COST > 0

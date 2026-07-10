"""Tests for backend/recommender/engine.py"""
from scanner.base import Finding
from recommender.engine import generate_recommendations, summarize


def _finding(resource_type, cost=10.0, resource_id="res-1"):
    return Finding(resource_id, resource_type, "ap-south-1", "test reason", monthly_cost=cost)


def test_known_finding_type_produces_recommendation():
    findings = [_finding("EC2:Idle", cost=25.0)]
    recs = generate_recommendations(findings)
    assert len(recs) == 1
    assert recs[0]["ResourceType"] == "EC2:Idle"
    assert recs[0]["Risk"] == "low"
    assert recs[0]["EstimatedMonthlySavings"] == 25.0
    assert "Downsize" in recs[0]["Recommendation"] or "schedule" in recs[0]["Recommendation"]


def test_unknown_finding_type_is_skipped():
    findings = [_finding("Totally:Unknown")]
    recs = generate_recommendations(findings)
    assert recs == []


def test_recommendations_sorted_by_savings_descending():
    findings = [
        _finding("EBS:Unattached", cost=5.0, resource_id="vol-a"),
        _finding("EC2:Stopped", cost=50.0, resource_id="i-b"),
        _finding("EIP:Unattached", cost=3.6, resource_id="eip-c"),
    ]
    recs = generate_recommendations(findings)
    savings = [r["EstimatedMonthlySavings"] for r in recs]
    assert savings == sorted(savings, reverse=True)


def test_critical_risk_assigned_for_public_s3():
    findings = [_finding("S3:PublicBucket", cost=0.0, resource_id="bucket-x")]
    recs = generate_recommendations(findings)
    assert recs[0]["Risk"] == "critical"


def test_summarize_totals_and_risk_breakdown():
    findings = [
        _finding("EC2:Idle", cost=20.0),
        _finding("S3:PublicBucket", cost=0.0, resource_id="bucket-y"),
    ]
    recs = generate_recommendations(findings)
    summary = summarize(recs)
    assert summary["total_findings"] == 2
    assert summary["total_potential_monthly_savings"] == 20.0
    assert summary["findings_by_risk"]["low"] == 1
    assert summary["findings_by_risk"]["critical"] == 1


def test_summarize_empty_list():
    summary = summarize([])
    assert summary["total_findings"] == 0
    assert summary["total_potential_monthly_savings"] == 0
    assert summary["findings_by_risk"] == {}

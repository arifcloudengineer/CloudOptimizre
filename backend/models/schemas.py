"""Pydantic models for API request/response validation."""
from typing import Optional, Literal
from pydantic import BaseModel


class Recommendation(BaseModel):
    ResourceID: str
    ResourceType: str
    Region: str
    Condition: str
    Recommendation: str
    Action: str
    Risk: Literal["low", "medium", "high", "critical"]
    EstimatedMonthlySavings: float
    Tags: dict = {}
    Metadata: dict = {}
    ScanDate: Optional[str] = None
    Status: Optional[str] = "open"


class ScanSummary(BaseModel):
    ScanID: str
    ScanDate: str
    total_findings: int
    total_potential_monthly_savings: float
    findings_by_risk: dict


class OptimizeRequest(BaseModel):
    resource_id: str
    action: str
    dry_run: bool = True


class OptimizeResponse(BaseModel):
    resource_id: str
    action: str
    dry_run: bool
    status: str
    detail: str


class CostSummary(BaseModel):
    total_monthly_spend_estimate: float
    total_potential_savings: float
    optimization_score: int  # 0-100, higher = more optimized
    critical_findings: int

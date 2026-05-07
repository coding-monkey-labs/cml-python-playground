"""Analytics schemas."""

from pydantic import BaseModel


class HotspotFeature(BaseModel):
    feature: str
    defect_count: int
    total_weight: float


class ReopenPattern(BaseModel):
    defect: str
    reopened_from: str
    summary: str


class DeveloperMetrics(BaseModel):
    email: str
    total_issues: int
    avg_resolution_hours: float | None
    reopen_rate: float
    fix_completeness: float


class FeatureHealthScore(BaseModel):
    feature_name: str
    health_score: float
    defect_density: float
    volatility_score: float
    regression_likelihood: float


class QualityIndex(BaseModel):
    feature_name: str
    health_score: float
    code_volatility: float
    regression_likelihood: float

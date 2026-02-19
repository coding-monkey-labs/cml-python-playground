"""Agent integration schemas."""

from pydantic import BaseModel


class AgentContextRequest(BaseModel):
    feature_name: str | None = None
    jira_key: str | None = None


class AgentContextResponse(BaseModel):
    feature_summary: str | None
    historical_defects: list[dict]
    reopen_history: list[dict]
    pr_history: list[dict]


class AgentRiskRequest(BaseModel):
    feature_name: str


class AgentRiskResponse(BaseModel):
    feature_name: str
    risk_score: float
    defect_count: int
    reopen_count: int
    past_failure_patterns: list[str]


class AgentDuplicateCheckRequest(BaseModel):
    summary: str
    description: str | None = None


class AgentDuplicateCheckResponse(BaseModel):
    similar_defects: list[dict]
    highest_confidence: float


class AgentReviewContextRequest(BaseModel):
    component_name: str | None = None
    file_paths: list[str] | None = None


class AgentReviewContextResponse(BaseModel):
    past_fixes: list[dict]
    linked_jira_summaries: list[str]
    risk_areas: list[str]

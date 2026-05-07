"""RAG schemas."""

from pydantic import BaseModel


class SimilarityQueryRequest(BaseModel):
    text: str
    n_results: int = 10
    filter_type: str | None = None


class SimilarityQueryResult(BaseModel):
    id: str
    document: str
    distance: float
    metadata: dict | None = None


class SimilarityQueryResponse(BaseModel):
    query: str
    results: list[SimilarityQueryResult]


class DuplicateCheckRequest(BaseModel):
    summary: str
    description: str | None = None
    threshold: float = 0.85


class DuplicateCheckResult(BaseModel):
    jira_key: str
    summary: str
    confidence: float
    is_likely_duplicate: bool


class DuplicateCheckResponse(BaseModel):
    input_summary: str
    duplicates: list[DuplicateCheckResult]


class DefectSummaryRequest(BaseModel):
    jira_key: str


class DefectSummaryResponse(BaseModel):
    jira_key: str
    summary: str
    similar_past_defects: list[str]
    suggested_root_cause: str | None
    recommended_fix_approach: str | None

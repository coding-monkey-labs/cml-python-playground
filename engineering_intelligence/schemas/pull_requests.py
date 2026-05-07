"""Pull request schemas."""

from datetime import datetime

from pydantic import BaseModel


class PRCreate(BaseModel):
    pr_number: int
    repo: str
    title: str
    description: str | None = None
    status: str = "open"
    author_email: str | None = None
    author_login: str | None = None
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0


class PRResponse(BaseModel):
    id: int
    pr_number: int
    repo: str
    title: str
    description: str | None
    status: str
    author_email: str | None
    author_login: str | None
    files_changed: int
    additions: int
    deletions: int
    merged_at: datetime | None
    pr_created_at: datetime | None

    model_config = {"from_attributes": True}


class PRMappingResponse(BaseModel):
    pr_number: int
    repo: str
    jira_keys: list[str]
    mapping_types: list[str]


class PRImpact(BaseModel):
    pr_number: int
    repo: str
    risk_score: float
    related_defects: int
    affected_features: list[str]

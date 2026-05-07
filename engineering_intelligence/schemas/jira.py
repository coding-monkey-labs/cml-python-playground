"""Jira schemas."""

from datetime import datetime

from pydantic import BaseModel


class JiraIssueCreate(BaseModel):
    jira_key: str
    issue_type: str
    summary: str
    description: str | None = None
    status: str = "open"
    priority: str | None = None
    severity: str | None = None
    assignee_email: str | None = None
    reporter_email: str | None = None
    parent_key: str | None = None
    epic_key: str | None = None
    labels: str | None = None
    components: str | None = None


class JiraIssueResponse(BaseModel):
    id: int
    jira_key: str
    issue_type: str
    summary: str
    description: str | None
    status: str
    priority: str | None
    severity: str | None
    assignee_email: str | None
    reporter_email: str | None
    parent_key: str | None
    epic_key: str | None
    reopen_count: int
    resolution_time_hours: float | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class JiraSearchRequest(BaseModel):
    query: str
    issue_type: str | None = None
    status: str | None = None
    epic_key: str | None = None
    limit: int = 20


class JiraSimilarityRequest(BaseModel):
    text: str
    n_results: int = 10
    issue_type: str | None = None


class JiraSimilarityResult(BaseModel):
    jira_key: str
    summary: str
    distance: float
    metadata: dict | None = None


class JiraGraphSubtree(BaseModel):
    root_key: str
    nodes: list[dict]

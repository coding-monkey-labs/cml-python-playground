"""Dashboard schemas — aggregated views for frontend consumption."""

from datetime import datetime

from pydantic import BaseModel


# ── Summary ───────────────────────────────────────────────────────────────────


class EntityCounts(BaseModel):
    features: int = 0
    jira_issues: int = 0
    pull_requests: int = 0
    defect_count: int = 0
    open_defects: int = 0


class WorkflowSummary(BaseModel):
    total_runs: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    active_schedules: int = 0


class DashboardSummary(BaseModel):
    entity_counts: EntityCounts
    workflow_summary: WorkflowSummary
    top_hotspots: list[dict]
    recent_defects: list[dict]
    system_health: str  # "healthy" | "degraded" | "unhealthy"


# ── Trends ────────────────────────────────────────────────────────────────────


class TrendPoint(BaseModel):
    period: str
    count: int


class DefectTrends(BaseModel):
    defects_created: list[TrendPoint]
    defects_resolved: list[TrendPoint]
    reopen_counts: list[TrendPoint]


# ── Activity Feed ─────────────────────────────────────────────────────────────


class ActivityItem(BaseModel):
    type: str  # "jira_created" | "pr_merged" | "workflow_completed" | ...
    title: str
    detail: str | None = None
    timestamp: datetime | None = None


# ── System Health ─────────────────────────────────────────────────────────────


class ServiceStatus(BaseModel):
    name: str
    status: str  # "up" | "down" | "degraded"
    latency_ms: float | None = None


class SystemHealth(BaseModel):
    overall: str  # "healthy" | "degraded" | "unhealthy"
    services: list[ServiceStatus]
    database_size_mb: float | None = None
    total_workflow_runs_24h: int = 0
    failed_workflow_runs_24h: int = 0

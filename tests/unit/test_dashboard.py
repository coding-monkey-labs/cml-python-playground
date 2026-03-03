"""Tests for dashboard schemas and data models."""

from datetime import datetime, timezone

from engineering_intelligence.schemas.dashboard import (
    ActivityItem,
    DashboardSummary,
    DefectTrends,
    EntityCounts,
    ServiceStatus,
    SystemHealth,
    TrendPoint,
    WorkflowSummary,
)


class TestEntityCounts:
    def test_defaults(self):
        counts = EntityCounts()
        assert counts.features == 0
        assert counts.jira_issues == 0
        assert counts.pull_requests == 0
        assert counts.defect_count == 0
        assert counts.open_defects == 0

    def test_with_values(self):
        counts = EntityCounts(
            features=10, jira_issues=200, pull_requests=50, defect_count=30, open_defects=8
        )
        assert counts.features == 10
        assert counts.open_defects == 8


class TestWorkflowSummary:
    def test_defaults(self):
        ws = WorkflowSummary()
        assert ws.total_runs == 0
        assert ws.active_schedules == 0

    def test_with_values(self):
        ws = WorkflowSummary(
            total_runs=100, running=2, completed=95, failed=3, active_schedules=4
        )
        assert ws.running == 2
        assert ws.active_schedules == 4


class TestDashboardSummary:
    def test_full_summary(self):
        summary = DashboardSummary(
            entity_counts=EntityCounts(features=5, jira_issues=50),
            workflow_summary=WorkflowSummary(total_runs=10, completed=8),
            top_hotspots=[
                {"feature": "Login", "defect_count": 15, "health_score": 40.0},
            ],
            recent_defects=[
                {"jira_key": "PROJ-100", "summary": "Bug", "status": "open", "priority": "High"},
            ],
            system_health="healthy",
        )
        assert summary.system_health == "healthy"
        assert len(summary.top_hotspots) == 1
        assert summary.entity_counts.features == 5

    def test_empty_summary(self):
        summary = DashboardSummary(
            entity_counts=EntityCounts(),
            workflow_summary=WorkflowSummary(),
            top_hotspots=[],
            recent_defects=[],
            system_health="healthy",
        )
        assert len(summary.top_hotspots) == 0


class TestDefectTrends:
    def test_empty_trends(self):
        trends = DefectTrends(
            defects_created=[], defects_resolved=[], reopen_counts=[]
        )
        assert len(trends.defects_created) == 0

    def test_with_data(self):
        trends = DefectTrends(
            defects_created=[
                TrendPoint(period="2026-Q1", count=10),
                TrendPoint(period="2025-Q4", count=8),
            ],
            defects_resolved=[
                TrendPoint(period="2026-Q1", count=7),
            ],
            reopen_counts=[
                TrendPoint(period="2026-Q1", count=2),
            ],
        )
        assert trends.defects_created[0].count == 10
        assert trends.reopen_counts[0].period == "2026-Q1"


class TestTrendPoint:
    def test_creation(self):
        tp = TrendPoint(period="2025-Q3", count=42)
        assert tp.period == "2025-Q3"
        assert tp.count == 42


class TestActivityItem:
    def test_minimal(self):
        item = ActivityItem(type="jira_defect", title="PROJ-123: Login broken")
        assert item.detail is None
        assert item.timestamp is None

    def test_full(self):
        now = datetime.now(timezone.utc)
        item = ActivityItem(
            type="pr_merged",
            title="PR #42: Fix login",
            detail="Repo: org/repo",
            timestamp=now,
        )
        assert item.type == "pr_merged"
        assert item.timestamp == now


class TestServiceStatus:
    def test_creation(self):
        ss = ServiceStatus(name="postgresql", status="up", latency_ms=1.5)
        assert ss.latency_ms == 1.5

    def test_no_latency(self):
        ss = ServiceStatus(name="neo4j", status="down")
        assert ss.latency_ms is None


class TestSystemHealth:
    def test_healthy(self):
        health = SystemHealth(
            overall="healthy",
            services=[ServiceStatus(name="postgresql", status="up")],
            total_workflow_runs_24h=50,
            failed_workflow_runs_24h=0,
        )
        assert health.overall == "healthy"
        assert len(health.services) == 1

    def test_degraded(self):
        health = SystemHealth(
            overall="degraded",
            services=[
                ServiceStatus(name="postgresql", status="up"),
                ServiceStatus(name="temporal", status="degraded"),
            ],
            total_workflow_runs_24h=50,
            failed_workflow_runs_24h=2,
        )
        assert health.overall == "degraded"
        assert health.failed_workflow_runs_24h == 2

    def test_defaults(self):
        health = SystemHealth(overall="healthy", services=[])
        assert health.database_size_mb is None
        assert health.total_workflow_runs_24h == 0
        assert health.failed_workflow_runs_24h == 0

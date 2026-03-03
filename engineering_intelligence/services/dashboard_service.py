"""Dashboard service — aggregates data from multiple tables for overview endpoints."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.db.models import (
    DefectMetrics,
    Feature,
    JiraIssue,
    JiraIssueType,
    JiraStatus,
    PullRequest,
    WorkflowRun,
    WorkflowSchedule,
    WorkflowStatus,
)
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


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Summary ───────────────────────────────────────────────────────────

    async def get_summary(self, hotspot_limit: int = 5) -> DashboardSummary:
        entity_counts = await self._get_entity_counts()
        workflow_summary = await self._get_workflow_summary()
        top_hotspots = await self._get_top_hotspots(hotspot_limit)
        recent_defects = await self._get_recent_defects(limit=5)
        system_health = await self._compute_system_health_label()

        return DashboardSummary(
            entity_counts=entity_counts,
            workflow_summary=workflow_summary,
            top_hotspots=top_hotspots,
            recent_defects=recent_defects,
            system_health=system_health,
        )

    async def _get_entity_counts(self) -> EntityCounts:
        feature_count = await self._count(Feature)
        jira_count = await self._count(JiraIssue)
        pr_count = await self._count(PullRequest)

        # Total defects
        defect_result = await self._db.execute(
            select(func.count(JiraIssue.id)).where(
                JiraIssue.issue_type == JiraIssueType.DEFECT
            )
        )
        defect_count = defect_result.scalar() or 0

        # Open defects
        open_result = await self._db.execute(
            select(func.count(JiraIssue.id)).where(
                JiraIssue.issue_type == JiraIssueType.DEFECT,
                JiraIssue.status.in_([JiraStatus.OPEN, JiraStatus.REOPENED, JiraStatus.IN_PROGRESS]),
            )
        )
        open_defects = open_result.scalar() or 0

        return EntityCounts(
            features=feature_count,
            jira_issues=jira_count,
            pull_requests=pr_count,
            defect_count=defect_count,
            open_defects=open_defects,
        )

    async def _get_workflow_summary(self) -> WorkflowSummary:
        total = await self._count(WorkflowRun)

        running_result = await self._db.execute(
            select(func.count(WorkflowRun.id)).where(
                WorkflowRun.status == WorkflowStatus.RUNNING
            )
        )
        running = running_result.scalar() or 0

        completed_result = await self._db.execute(
            select(func.count(WorkflowRun.id)).where(
                WorkflowRun.status == WorkflowStatus.COMPLETED
            )
        )
        completed = completed_result.scalar() or 0

        failed_result = await self._db.execute(
            select(func.count(WorkflowRun.id)).where(
                WorkflowRun.status == WorkflowStatus.FAILED
            )
        )
        failed = failed_result.scalar() or 0

        # Count active schedules
        active_schedules_result = await self._db.execute(
            select(func.count(WorkflowSchedule.id)).where(
                WorkflowSchedule.is_enabled.is_(True)
            )
        )
        active_schedules = active_schedules_result.scalar() or 0

        return WorkflowSummary(
            total_runs=total,
            running=running,
            completed=completed,
            failed=failed,
            active_schedules=active_schedules,
        )

    async def _get_top_hotspots(self, limit: int) -> list[dict]:
        result = await self._db.execute(
            select(Feature.name, Feature.defect_count, Feature.health_score)
            .where(Feature.defect_count > 0)
            .order_by(Feature.defect_count.desc())
            .limit(limit)
        )
        return [
            {
                "feature": row.name,
                "defect_count": row.defect_count,
                "health_score": row.health_score,
            }
            for row in result.all()
        ]

    async def _get_recent_defects(self, limit: int) -> list[dict]:
        result = await self._db.execute(
            select(JiraIssue.jira_key, JiraIssue.summary, JiraIssue.status, JiraIssue.priority)
            .where(JiraIssue.issue_type == JiraIssueType.DEFECT)
            .order_by(JiraIssue.created_at.desc())
            .limit(limit)
        )
        return [
            {
                "jira_key": row.jira_key,
                "summary": row.summary,
                "status": row.status.value if row.status else None,
                "priority": row.priority,
            }
            for row in result.all()
        ]

    async def _compute_system_health_label(self) -> str:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        failed_result = await self._db.execute(
            select(func.count(WorkflowRun.id)).where(
                WorkflowRun.status == WorkflowStatus.FAILED,
                WorkflowRun.created_at >= cutoff,
            )
        )
        recent_failures = failed_result.scalar() or 0

        if recent_failures == 0:
            return "healthy"
        elif recent_failures <= 3:
            return "degraded"
        return "unhealthy"

    # ── Trends ────────────────────────────────────────────────────────────

    async def get_defect_trends(self, periods: int = 6) -> DefectTrends:
        """Return defect counts grouped by period from DefectMetrics table."""
        result = await self._db.execute(
            select(DefectMetrics.period, DefectMetrics.defect_count, DefectMetrics.reopen_count)
            .order_by(DefectMetrics.period.desc())
            .limit(periods)
        )
        rows = result.all()

        created = [TrendPoint(period=r.period, count=r.defect_count) for r in reversed(rows)]
        resolved: list[TrendPoint] = []  # Requires additional data source
        reopens = [TrendPoint(period=r.period, count=r.reopen_count) for r in reversed(rows)]

        return DefectTrends(
            defects_created=created,
            defects_resolved=resolved,
            reopen_counts=reopens,
        )

    # ── Activity Feed ─────────────────────────────────────────────────────

    async def get_recent_activity(self, limit: int = 20) -> list[ActivityItem]:
        """Combine recent events from multiple tables into a single feed."""
        activities: list[ActivityItem] = []

        # Recent Jira issues
        jira_result = await self._db.execute(
            select(JiraIssue.jira_key, JiraIssue.summary, JiraIssue.issue_type, JiraIssue.created_at)
            .order_by(JiraIssue.created_at.desc())
            .limit(limit)
        )
        for row in jira_result.all():
            activities.append(
                ActivityItem(
                    type=f"jira_{row.issue_type.value}",
                    title=f"{row.jira_key}: {row.summary}",
                    detail=f"Type: {row.issue_type.value}",
                    timestamp=row.created_at,
                )
            )

        # Recent PRs
        pr_result = await self._db.execute(
            select(
                PullRequest.pr_number,
                PullRequest.repo,
                PullRequest.title,
                PullRequest.status,
                PullRequest.created_at,
            )
            .order_by(PullRequest.created_at.desc())
            .limit(limit)
        )
        for row in pr_result.all():
            activities.append(
                ActivityItem(
                    type=f"pr_{row.status.value}",
                    title=f"PR #{row.pr_number}: {row.title}",
                    detail=f"Repo: {row.repo}",
                    timestamp=row.created_at,
                )
            )

        # Recent workflow runs
        wf_result = await self._db.execute(
            select(
                WorkflowRun.workflow_type,
                WorkflowRun.workflow_id,
                WorkflowRun.status,
                WorkflowRun.created_at,
            )
            .order_by(WorkflowRun.created_at.desc())
            .limit(limit)
        )
        for row in wf_result.all():
            activities.append(
                ActivityItem(
                    type=f"workflow_{row.status.value}",
                    title=f"Workflow: {row.workflow_type}",
                    detail=f"ID: {row.workflow_id}, Status: {row.status.value}",
                    timestamp=row.created_at,
                )
            )

        # Sort all by timestamp descending, take top N
        activities.sort(key=lambda a: a.timestamp or datetime.min, reverse=True)
        return activities[:limit]

    # ── System Health ─────────────────────────────────────────────────────

    async def get_system_health(self) -> SystemHealth:
        services: list[ServiceStatus] = []

        # Check DB connectivity (we're already connected if we got here)
        services.append(ServiceStatus(name="postgresql", status="up", latency_ms=None))

        # Workflow stats for last 24h
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        total_result = await self._db.execute(
            select(func.count(WorkflowRun.id)).where(WorkflowRun.created_at >= cutoff)
        )
        total_24h = total_result.scalar() or 0

        failed_result = await self._db.execute(
            select(func.count(WorkflowRun.id)).where(
                WorkflowRun.status == WorkflowStatus.FAILED,
                WorkflowRun.created_at >= cutoff,
            )
        )
        failed_24h = failed_result.scalar() or 0

        overall = "healthy"
        if failed_24h > 0:
            overall = "degraded" if failed_24h <= 3 else "unhealthy"

        return SystemHealth(
            overall=overall,
            services=services,
            database_size_mb=None,
            total_workflow_runs_24h=total_24h,
            failed_workflow_runs_24h=failed_24h,
        )

    # ── Helpers ────────────────────────────────────────────────────────────

    async def _count(self, model) -> int:
        result = await self._db.execute(select(func.count(model.id)))
        return result.scalar() or 0

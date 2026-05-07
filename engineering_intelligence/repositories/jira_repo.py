"""Jira issue repository."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.db.models import JiraIssue, JiraIssueType, JiraStatus


class JiraRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_key(self, jira_key: str) -> JiraIssue | None:
        result = await self._db.execute(
            select(JiraIssue).where(JiraIssue.jira_key == jira_key)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, issue_id: int) -> JiraIssue | None:
        result = await self._db.execute(
            select(JiraIssue).where(JiraIssue.id == issue_id)
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        query: str | None = None,
        issue_type: str | None = None,
        status: str | None = None,
        epic_key: str | None = None,
        limit: int = 20,
    ) -> list[JiraIssue]:
        stmt = select(JiraIssue)
        if query:
            stmt = stmt.where(
                JiraIssue.summary.ilike(f"%{query}%")
                | JiraIssue.description.ilike(f"%{query}%")
            )
        if issue_type:
            stmt = stmt.where(JiraIssue.issue_type == JiraIssueType(issue_type))
        if status:
            stmt = stmt.where(JiraIssue.status == JiraStatus(status))
        if epic_key:
            stmt = stmt.where(JiraIssue.epic_key == epic_key)
        stmt = stmt.limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def upsert(self, issue: JiraIssue) -> JiraIssue:
        existing = await self.get_by_key(issue.jira_key)
        if existing:
            for attr in [
                "summary", "description", "status", "priority", "severity",
                "assignee_email", "reporter_email", "parent_key", "epic_key",
                "resolution", "resolution_notes", "reopen_count",
                "resolution_time_hours", "labels", "components",
                "jira_created_at", "jira_updated_at",
            ]:
                val = getattr(issue, attr, None)
                if val is not None:
                    setattr(existing, attr, val)
            await self._db.flush()
            return existing
        self._db.add(issue)
        await self._db.flush()
        return issue

    async def get_children(self, parent_key: str) -> list[JiraIssue]:
        result = await self._db.execute(
            select(JiraIssue).where(JiraIssue.parent_key == parent_key)
        )
        return list(result.scalars().all())

    async def get_by_epic(self, epic_key: str) -> list[JiraIssue]:
        result = await self._db.execute(
            select(JiraIssue).where(JiraIssue.epic_key == epic_key)
        )
        return list(result.scalars().all())

    async def count_defects_by_feature(self) -> list[dict]:
        """Aggregate defect counts for analytics."""
        stmt = (
            select(
                JiraIssue.epic_key,
                func.count(JiraIssue.id).label("defect_count"),
                func.avg(JiraIssue.resolution_time_hours).label("avg_resolution"),
                func.sum(JiraIssue.reopen_count).label("total_reopens"),
            )
            .where(JiraIssue.issue_type == JiraIssueType.DEFECT)
            .group_by(JiraIssue.epic_key)
        )
        result = await self._db.execute(stmt)
        return [dict(row._mapping) for row in result.all()]

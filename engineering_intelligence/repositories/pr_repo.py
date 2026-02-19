"""Pull request repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.db.models import PullRequest, JiraPRMapping


class PRRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_number(self, pr_number: int, repo: str) -> PullRequest | None:
        result = await self._db.execute(
            select(PullRequest).where(
                PullRequest.pr_number == pr_number,
                PullRequest.repo == repo,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, pr_id: int) -> PullRequest | None:
        result = await self._db.execute(
            select(PullRequest).where(PullRequest.id == pr_id)
        )
        return result.scalar_one_or_none()

    async def search(self, query: str | None = None, repo: str | None = None,
                     limit: int = 20) -> list[PullRequest]:
        stmt = select(PullRequest)
        if query:
            stmt = stmt.where(
                PullRequest.title.ilike(f"%{query}%")
                | PullRequest.description.ilike(f"%{query}%")
            )
        if repo:
            stmt = stmt.where(PullRequest.repo == repo)
        stmt = stmt.order_by(PullRequest.pr_created_at.desc()).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def upsert(self, pr: PullRequest) -> PullRequest:
        existing = await self.get_by_number(pr.pr_number, pr.repo)
        if existing:
            for attr in ["title", "description", "status", "author_email",
                         "author_login", "files_changed", "additions",
                         "deletions", "merged_at"]:
                val = getattr(pr, attr, None)
                if val is not None:
                    setattr(existing, attr, val)
            await self._db.flush()
            return existing
        self._db.add(pr)
        await self._db.flush()
        return pr

    async def get_mappings(self, pr_id: int) -> list[JiraPRMapping]:
        result = await self._db.execute(
            select(JiraPRMapping).where(JiraPRMapping.pull_request_id == pr_id)
        )
        return list(result.scalars().all())

    async def add_jira_mapping(self, pr_id: int, jira_issue_id: int,
                               mapping_type: str = "explicit",
                               confidence: float = 1.0) -> JiraPRMapping:
        mapping = JiraPRMapping(
            pull_request_id=pr_id,
            jira_issue_id=jira_issue_id,
            mapping_type=mapping_type,
            confidence=confidence,
        )
        self._db.add(mapping)
        await self._db.flush()
        return mapping

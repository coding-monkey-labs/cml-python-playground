"""Pull request service — PR ingestion, mapping, and risk scoring."""

from engineering_intelligence.db.models import PullRequest
from engineering_intelligence.graph.repository import GraphRepository
from engineering_intelligence.repositories.jira_repo import JiraRepository
from engineering_intelligence.repositories.pr_repo import PRRepository
from engineering_intelligence.schemas.pull_requests import (
    PRCreate,
    PRImpact,
    PRMappingResponse,
    PRResponse,
)
from engineering_intelligence.services.jira_service import JiraService


class PRService:
    def __init__(
        self,
        pr_repo: PRRepository,
        jira_repo: JiraRepository | None = None,
        graph_repo: GraphRepository | None = None,
    ) -> None:
        self._repo = pr_repo
        self._jira_repo = jira_repo
        self._graph = graph_repo

    async def upsert_pr(self, data: PRCreate) -> PRResponse:
        pr = PullRequest(
            pr_number=data.pr_number,
            repo=data.repo,
            title=data.title,
            description=data.description,
            status=data.status,
            author_email=data.author_email,
            author_login=data.author_login,
            files_changed=data.files_changed,
            additions=data.additions,
            deletions=data.deletions,
        )
        pr = await self._repo.upsert(pr)

        # Extract Jira keys and create mappings
        jira_keys = JiraService.extract_jira_keys(
            f"{data.title} {data.description or ''}"
        )
        if self._jira_repo:
            for key in jira_keys:
                jira_issue = await self._jira_repo.get_by_key(key)
                if jira_issue:
                    await self._repo.add_jira_mapping(
                        pr_id=pr.id,
                        jira_issue_id=jira_issue.id,
                        mapping_type="explicit",
                    )
                    if self._graph:
                        await self._graph.link_pr_fixes_jira(pr.pr_number, key)

        return PRResponse.model_validate(pr)

    async def search(self, query: str | None = None,
                     repo: str | None = None,
                     limit: int = 20) -> list[PRResponse]:
        prs = await self._repo.search(query=query, repo=repo, limit=limit)
        return [PRResponse.model_validate(pr) for pr in prs]

    async def get_pr(self, pr_number: int, repo: str) -> PRResponse | None:
        pr = await self._repo.get_by_number(pr_number, repo)
        if not pr:
            return None
        return PRResponse.model_validate(pr)

    async def get_mappings(self, pr_number: int, repo: str) -> PRMappingResponse | None:
        pr = await self._repo.get_by_number(pr_number, repo)
        if not pr:
            return None
        mappings = await self._repo.get_mappings(pr.id)
        jira_keys = []
        mapping_types = []
        if self._jira_repo:
            for m in mappings:
                issue = await self._jira_repo.get_by_key_id(m.jira_issue_id)
                if issue:
                    jira_keys.append(issue.jira_key)
                    mapping_types.append(m.mapping_type)
        return PRMappingResponse(
            pr_number=pr.pr_number,
            repo=pr.repo,
            jira_keys=jira_keys,
            mapping_types=mapping_types,
        )

    async def get_impact(self, pr_number: int, repo: str) -> PRImpact | None:
        pr = await self._repo.get_by_number(pr_number, repo)
        if not pr:
            return None
        # Basic risk scoring: larger changes = higher risk
        size_score = min(1.0, (pr.files_changed * 0.1 + pr.additions * 0.01))
        return PRImpact(
            pr_number=pr.pr_number,
            repo=pr.repo,
            risk_score=round(size_score, 2),
            related_defects=0,
            affected_features=[],
        )

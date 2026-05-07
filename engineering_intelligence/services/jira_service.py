"""Jira service — handles ingestion, search, and graph operations."""

import json
import re

import httpx

from engineering_intelligence.config import get_settings
from engineering_intelligence.db.models import JiraIssue, JiraIssueType, JiraStatus
from engineering_intelligence.graph.repository import GraphRepository
from engineering_intelligence.repositories.jira_repo import JiraRepository
from engineering_intelligence.schemas.jira import (
    JiraIssueCreate,
    JiraIssueResponse,
    JiraSearchRequest,
)


class JiraService:
    def __init__(
        self,
        jira_repo: JiraRepository,
        graph_repo: GraphRepository | None = None,
    ) -> None:
        self._repo = jira_repo
        self._graph = graph_repo
        self._settings = get_settings()

    # ── CRUD ───────────────────────────────────────────────────────────────

    async def get_issue(self, jira_key: str) -> JiraIssueResponse | None:
        issue = await self._repo.get_by_key(jira_key)
        if not issue:
            return None
        return JiraIssueResponse.model_validate(issue)

    async def search(self, request: JiraSearchRequest) -> list[JiraIssueResponse]:
        issues = await self._repo.search(
            query=request.query,
            issue_type=request.issue_type,
            status=request.status,
            epic_key=request.epic_key,
            limit=request.limit,
        )
        return [JiraIssueResponse.model_validate(i) for i in issues]

    async def upsert_issue(self, data: JiraIssueCreate) -> JiraIssueResponse:
        issue = JiraIssue(
            jira_key=data.jira_key,
            issue_type=JiraIssueType(data.issue_type),
            summary=data.summary,
            description=data.description,
            status=JiraStatus(data.status),
            priority=data.priority,
            severity=data.severity,
            assignee_email=data.assignee_email,
            reporter_email=data.reporter_email,
            parent_key=data.parent_key,
            epic_key=data.epic_key,
            labels=data.labels,
            components=data.components,
        )
        issue = await self._repo.upsert(issue)

        # Update graph if available
        if self._graph:
            await self._graph.upsert_jira_node(
                key=issue.jira_key,
                issue_type=issue.issue_type.value,
                summary=issue.summary,
                status=issue.status.value,
                severity=issue.severity,
            )
            # Link to parent in graph
            if issue.epic_key:
                await self._graph.link_epic_child(
                    epic_key=issue.epic_key,
                    child_key=issue.jira_key,
                    child_type=issue.issue_type.value,
                )
            if issue.parent_key and issue.parent_key != issue.epic_key:
                await self._graph.link_story_child(
                    story_key=issue.parent_key,
                    child_key=issue.jira_key,
                    child_type=issue.issue_type.value,
                )
            # Link developer
            if issue.assignee_email:
                await self._graph.link_developer(
                    email=issue.assignee_email, jira_key=issue.jira_key
                )
            # Link components
            if issue.components:
                try:
                    components = json.loads(issue.components)
                    for comp in components:
                        await self._graph.link_component(
                            jira_key=issue.jira_key, component_name=comp
                        )
                except (json.JSONDecodeError, TypeError):
                    pass

        return JiraIssueResponse.model_validate(issue)

    async def get_subtree(self, root_key: str) -> list[dict]:
        if self._graph:
            return await self._graph.get_jira_subtree(root_key)
        # Fallback to relational DB
        children = await self._repo.get_children(root_key)
        return [{"key": c.jira_key, "summary": c.summary, "type": c.issue_type.value}
                for c in children]

    # ── External Jira API Fetching ─────────────────────────────────────────

    async def fetch_from_jira_api(self, epic_key: str) -> list[JiraIssueCreate]:
        """Fetch issues from Jira REST API for a given epic."""
        if not self._settings.jira_api_token:
            return []

        jql = f'("Epic Link" = {epic_key} OR parent = {epic_key}) ORDER BY created ASC'
        url = f"{self._settings.jira_base_url}/rest/api/2/search"
        headers = {
            "Authorization": f"Bearer {self._settings.jira_api_token}",
            "Content-Type": "application/json",
        }

        results: list[JiraIssueCreate] = []
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url, headers=headers, params={"jql": jql, "maxResults": 100}
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            for raw_issue in data.get("issues", []):
                fields = raw_issue.get("fields", {})
                issue_type_name = fields.get("issuetype", {}).get("name", "task").lower()
                issue_type = self._map_issue_type(issue_type_name)
                components = [c.get("name") for c in fields.get("components", [])]
                labels = fields.get("labels", [])
                results.append(JiraIssueCreate(
                    jira_key=raw_issue["key"],
                    issue_type=issue_type,
                    summary=fields.get("summary", ""),
                    description=fields.get("description"),
                    status=self._map_status(fields.get("status", {}).get("name", "open")),
                    priority=fields.get("priority", {}).get("name"),
                    assignee_email=fields.get("assignee", {}).get("emailAddress") if fields.get("assignee") else None,
                    reporter_email=fields.get("reporter", {}).get("emailAddress") if fields.get("reporter") else None,
                    epic_key=epic_key,
                    components=json.dumps(components) if components else None,
                    labels=json.dumps(labels) if labels else None,
                ))
        return results

    @staticmethod
    def extract_jira_keys(text: str) -> list[str]:
        """Extract Jira issue keys from arbitrary text (PR titles, descriptions)."""
        return re.findall(r"[A-Z][A-Z0-9]+-\d+", text)

    @staticmethod
    def _map_issue_type(name: str) -> str:
        mapping = {
            "epic": "epic", "story": "story", "task": "task",
            "bug": "defect", "defect": "defect", "sub-task": "sub_task",
        }
        return mapping.get(name.lower(), "task")

    @staticmethod
    def _map_status(name: str) -> str:
        mapping = {
            "to do": "open", "open": "open",
            "in progress": "in_progress", "in review": "in_review",
            "done": "resolved", "resolved": "resolved",
            "closed": "closed", "reopened": "reopened",
        }
        return mapping.get(name.lower(), "open")

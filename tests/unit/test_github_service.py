"""Tests for GitHubService — PR state mapping and key extraction."""

from engineering_intelligence.services.github_service import _map_pr_state, GitHubService
from engineering_intelligence.schemas.pull_requests import PRCreate


class TestPRStateMapping:
    def test_open(self):
        assert _map_pr_state("open", None) == "open"

    def test_merged(self):
        assert _map_pr_state("closed", "2024-01-15T10:00:00Z") == "merged"

    def test_closed_not_merged(self):
        assert _map_pr_state("closed", None) == "closed"

    def test_open_with_merged_at(self):
        # If merged_at is set, always return merged
        assert _map_pr_state("open", "2024-01-15T10:00:00Z") == "merged"


class TestParsePR:
    def test_parse_pr_basic(self):
        data = {
            "number": 42,
            "title": "Fix PROJ-123: login button",
            "body": "This fixes the login button issue",
            "state": "open",
            "merged_at": None,
            "changed_files": 3,
            "additions": 50,
            "deletions": 10,
            "user": {"login": "developer", "email": "dev@example.com"},
        }
        pr = GitHubService._parse_pr(data, "org/repo")
        assert pr.pr_number == 42
        assert pr.repo == "org/repo"
        assert pr.title == "Fix PROJ-123: login button"
        assert pr.status == "open"
        assert pr.author_login == "developer"

    def test_parse_merged_pr(self):
        data = {
            "number": 100,
            "title": "Feature: new dashboard",
            "body": None,
            "state": "closed",
            "merged_at": "2024-01-15T10:00:00Z",
            "changed_files": 10,
            "additions": 200,
            "deletions": 50,
            "user": {"login": "dev"},
        }
        pr = GitHubService._parse_pr(data, "org/repo")
        assert pr.status == "merged"

    def test_extract_jira_keys(self):
        service = GitHubService()
        pr = PRCreate(
            pr_number=1,
            repo="org/repo",
            title="Fix PROJ-42 AUTH-100: multi-fix",
            description="Also related to UI-5",
        )
        keys = service.extract_jira_keys_from_pr(pr)
        assert "PROJ-42" in keys
        assert "AUTH-100" in keys
        assert "UI-5" in keys


class TestWorkflowDispatch:
    def test_supported_workflows(self):
        from engineering_intelligence.workflows.dispatch import get_supported_workflows
        types = get_supported_workflows()
        assert "jira_ingestion" in types
        assert "pr_ingestion" in types
        assert "feature_graph_build" in types
        assert "hotspot_computation" in types
        assert "rag_rebuild" in types

    def test_build_workflow_args(self):
        from engineering_intelligence.workflows.dispatch import _build_workflow_args

        # Jira ingestion
        args = _build_workflow_args("jira_ingestion", {"epic_keys": ["PROJ-1"]})
        assert args == ["PROJ-1"]

        # PR ingestion
        args = _build_workflow_args("pr_ingestion", {"repo": "org/repo"})
        assert args == "org/repo"

        # Feature graph build
        args = _build_workflow_args("feature_graph_build", {"codebase_path": "/app"})
        assert args == "/app"

        # RAG rebuild
        args = _build_workflow_args("rag_rebuild", {})
        assert args is None

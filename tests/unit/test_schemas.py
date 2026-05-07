"""Tests for Pydantic schemas — validation and serialization."""

import pytest
from pydantic import ValidationError

from engineering_intelligence.schemas.auth import LoginRequest, UserCreate, UserResponse
from engineering_intelligence.schemas.jira import JiraIssueCreate, JiraSearchRequest
from engineering_intelligence.schemas.features import FeatureCreate, FeatureMetrics
from engineering_intelligence.schemas.pull_requests import PRCreate, PRImpact
from engineering_intelligence.schemas.rag import (
    DuplicateCheckRequest,
    SimilarityQueryRequest,
)
from engineering_intelligence.schemas.agent import AgentRiskRequest, AgentContextRequest
from engineering_intelligence.schemas.analytics import HotspotFeature, DeveloperMetrics


class TestAuthSchemas:
    def test_login_request_valid(self):
        req = LoginRequest(email="user@example.com", password="pass123")
        assert req.email == "user@example.com"

    def test_login_request_invalid_email(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="pass123")

    def test_user_create(self):
        user = UserCreate(
            email="new@example.com",
            password="secret",
            full_name="Test User",
        )
        assert user.role == "developer"

    def test_user_response_from_attributes(self):
        resp = UserResponse(
            id=1, email="u@x.com", full_name="Test", role="developer", is_active=True
        )
        assert resp.id == 1


class TestJiraSchemas:
    def test_jira_issue_create(self):
        issue = JiraIssueCreate(
            jira_key="PROJ-123",
            issue_type="defect",
            summary="Login button broken",
        )
        assert issue.status == "open"
        assert issue.severity is None

    def test_jira_search_request_defaults(self):
        req = JiraSearchRequest(query="login")
        assert req.limit == 20
        assert req.issue_type is None


class TestFeatureSchemas:
    def test_feature_create_minimal(self):
        f = FeatureCreate(name="Authentication")
        assert f.parent_id is None
        assert f.file_path is None

    def test_feature_metrics(self):
        m = FeatureMetrics(
            feature_name="Auth",
            defect_count=5,
            reopen_count=2,
            defect_density=0.33,
            health_score=75.0,
        )
        assert m.health_score == 75.0


class TestPRSchemas:
    def test_pr_create(self):
        pr = PRCreate(
            pr_number=42,
            repo="org/repo",
            title="Fix PROJ-123: login button",
        )
        assert pr.status == "open"
        assert pr.files_changed == 0

    def test_pr_impact(self):
        impact = PRImpact(
            pr_number=42,
            repo="org/repo",
            risk_score=0.7,
            related_defects=3,
            affected_features=["Auth", "Login"],
        )
        assert len(impact.affected_features) == 2


class TestRAGSchemas:
    def test_similarity_query(self):
        req = SimilarityQueryRequest(text="login button not working")
        assert req.n_results == 10
        assert req.filter_type is None

    def test_duplicate_check(self):
        req = DuplicateCheckRequest(
            summary="Login fails on Chrome",
            threshold=0.9,
        )
        assert req.threshold == 0.9


class TestAgentSchemas:
    def test_agent_risk_request(self):
        req = AgentRiskRequest(feature_name="Authentication")
        assert req.feature_name == "Authentication"

    def test_agent_context_request(self):
        req = AgentContextRequest(feature_name="Login", jira_key="PROJ-100")
        assert req.feature_name == "Login"


class TestAnalyticsSchemas:
    def test_hotspot_feature(self):
        h = HotspotFeature(feature="Login", defect_count=15, total_weight=45.5)
        assert h.total_weight == 45.5

    def test_developer_metrics(self):
        m = DeveloperMetrics(
            email="dev@example.com",
            total_issues=50,
            avg_resolution_hours=4.5,
            reopen_rate=0.1,
            fix_completeness=0.95,
        )
        assert m.fix_completeness == 0.95

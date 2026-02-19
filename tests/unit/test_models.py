"""Tests for SQLAlchemy models — enum values and defaults."""

from engineering_intelligence.db.models import (
    JiraIssueType,
    JiraStatus,
    PRStatus,
    UserRole,
    WorkflowStatus,
)


class TestEnums:
    def test_user_roles(self):
        assert UserRole.DEVELOPER.value == "developer"
        assert UserRole.ADMIN.value == "admin"

    def test_jira_issue_types(self):
        assert JiraIssueType.EPIC.value == "epic"
        assert JiraIssueType.STORY.value == "story"
        assert JiraIssueType.TASK.value == "task"
        assert JiraIssueType.DEFECT.value == "defect"
        assert JiraIssueType.SUB_TASK.value == "sub_task"

    def test_jira_statuses(self):
        assert JiraStatus.OPEN.value == "open"
        assert JiraStatus.IN_PROGRESS.value == "in_progress"
        assert JiraStatus.REOPENED.value == "reopened"
        assert JiraStatus.CLOSED.value == "closed"

    def test_pr_statuses(self):
        assert PRStatus.OPEN.value == "open"
        assert PRStatus.MERGED.value == "merged"
        assert PRStatus.CLOSED.value == "closed"

    def test_workflow_statuses(self):
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"

"""Tests for JiraService — key extraction and type mapping."""

from engineering_intelligence.services.jira_service import JiraService


class TestJiraKeyExtraction:
    def test_extract_from_pr_title(self):
        keys = JiraService.extract_jira_keys("Fix PROJ-123: login button broken")
        assert keys == ["PROJ-123"]

    def test_extract_multiple_keys(self):
        keys = JiraService.extract_jira_keys(
            "PROJ-123 PROJ-456: multi-fix for auth and dashboard"
        )
        assert keys == ["PROJ-123", "PROJ-456"]

    def test_extract_from_description(self):
        text = """
        This PR fixes several issues:
        - AUTH-42: token refresh
        - UI-100: button alignment
        Related to CORE-7
        """
        keys = JiraService.extract_jira_keys(text)
        assert "AUTH-42" in keys
        assert "UI-100" in keys
        assert "CORE-7" in keys

    def test_no_keys_found(self):
        keys = JiraService.extract_jira_keys("Just a regular commit message")
        assert keys == []

    def test_case_sensitive(self):
        keys = JiraService.extract_jira_keys("proj-123 should not match")
        assert keys == []


class TestIssueTypeMapping:
    def test_map_bug(self):
        assert JiraService._map_issue_type("Bug") == "defect"

    def test_map_story(self):
        assert JiraService._map_issue_type("Story") == "story"

    def test_map_subtask(self):
        assert JiraService._map_issue_type("Sub-Task") == "sub_task"

    def test_map_unknown_defaults_to_task(self):
        assert JiraService._map_issue_type("Custom Type") == "task"


class TestStatusMapping:
    def test_map_todo(self):
        assert JiraService._map_status("To Do") == "open"

    def test_map_in_progress(self):
        assert JiraService._map_status("In Progress") == "in_progress"

    def test_map_done(self):
        assert JiraService._map_status("Done") == "resolved"

    def test_map_unknown_defaults_to_open(self):
        assert JiraService._map_status("Unknown Status") == "open"

"""Tests for schedule schemas, cron presets, and repository logic."""

import json

import pytest
from pydantic import ValidationError

from engineering_intelligence.schemas.schedule import (
    CRON_PRESETS,
    ScheduleCreateRequest,
    ScheduleResponse,
    ScheduleUpdateRequest,
    resolve_cron,
)


class TestCronPresets:
    def test_presets_contain_expected_keys(self):
        assert "every_hour" in CRON_PRESETS
        assert "daily_midnight" in CRON_PRESETS
        assert "daily_2am" in CRON_PRESETS
        assert "weekly_sunday" in CRON_PRESETS
        assert "weekly_monday" in CRON_PRESETS
        assert "every_6_hours" in CRON_PRESETS

    def test_preset_values_are_valid_cron(self):
        for name, cron in CRON_PRESETS.items():
            parts = cron.split()
            assert len(parts) == 5, f"Preset '{name}' should have 5 cron fields"

    def test_resolve_cron_preset(self):
        assert resolve_cron("daily_midnight") == "0 0 * * *"
        assert resolve_cron("every_hour") == "0 * * * *"
        assert resolve_cron("weekly_monday") == "0 0 * * 1"

    def test_resolve_cron_passthrough(self):
        assert resolve_cron("*/15 * * * *") == "*/15 * * * *"
        assert resolve_cron("0 3 * * 5") == "0 3 * * 5"

    def test_resolve_cron_unknown_preset_returns_as_is(self):
        assert resolve_cron("not_a_preset") == "not_a_preset"


class TestScheduleCreateRequest:
    def test_valid_create(self):
        req = ScheduleCreateRequest(
            name="nightly-jira-sync",
            workflow_type="jira_incremental",
            cron_expression="daily_midnight",
        )
        assert req.name == "nightly-jira-sync"
        assert req.is_enabled is True
        assert req.params is None

    def test_create_with_params(self):
        req = ScheduleCreateRequest(
            name="hourly-hotspot",
            workflow_type="hotspot_computation",
            cron_expression="every_hour",
            params={"feature_names": ["Auth", "Login"]},
        )
        assert req.params == {"feature_names": ["Auth", "Login"]}

    def test_create_disabled(self):
        req = ScheduleCreateRequest(
            name="weekly-rag",
            workflow_type="rag_rebuild",
            cron_expression="weekly_sunday",
            is_enabled=False,
        )
        assert req.is_enabled is False

    def test_create_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            ScheduleCreateRequest(
                name="",
                workflow_type="jira_incremental",
                cron_expression="0 0 * * *",
            )


class TestScheduleUpdateRequest:
    def test_all_none_valid(self):
        req = ScheduleUpdateRequest()
        assert req.cron_expression is None
        assert req.params is None
        assert req.is_enabled is None

    def test_partial_update(self):
        req = ScheduleUpdateRequest(cron_expression="0 3 * * *", is_enabled=False)
        assert req.cron_expression == "0 3 * * *"
        assert req.is_enabled is False


class TestScheduleResponse:
    def test_from_dict(self):
        resp = ScheduleResponse(
            id=1,
            name="nightly-sync",
            workflow_type="jira_incremental",
            cron_expression="0 0 * * *",
            is_enabled=True,
        )
        assert resp.id == 1
        assert resp.temporal_schedule_id is None
        assert resp.last_run_at is None

    def test_with_all_fields(self):
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        resp = ScheduleResponse(
            id=2,
            name="hourly-hotspot",
            workflow_type="hotspot_computation",
            cron_expression="0 * * * *",
            params={"feature_names": ["Auth"]},
            is_enabled=True,
            temporal_schedule_id="schedule-hourly-hotspot",
            last_run_at=now,
            next_run_at=now,
            created_at=now,
            updated_at=now,
        )
        assert resp.temporal_schedule_id == "schedule-hourly-hotspot"
        assert resp.params == {"feature_names": ["Auth"]}

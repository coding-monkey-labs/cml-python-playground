"""Workflow schedule schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


CRON_PRESETS = {
    "every_hour": "0 * * * *",
    "every_6_hours": "0 */6 * * *",
    "daily_midnight": "0 0 * * *",
    "daily_2am": "0 2 * * *",
    "weekly_sunday": "0 0 * * 0",
    "weekly_monday": "0 0 * * 1",
}


def resolve_cron(expression: str) -> str:
    """Resolve a preset name to a cron expression, or return as-is."""
    return CRON_PRESETS.get(expression, expression)


class ScheduleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    workflow_type: str
    cron_expression: str = Field(
        ...,
        description="Cron expression (e.g. '0 2 * * *') or preset name "
        "(every_hour, daily_midnight, daily_2am, weekly_sunday, weekly_monday)",
    )
    params: dict | None = None
    is_enabled: bool = True


class ScheduleUpdateRequest(BaseModel):
    cron_expression: str | None = None
    params: dict | None = None
    is_enabled: bool | None = None


class ScheduleResponse(BaseModel):
    id: int
    name: str
    workflow_type: str
    cron_expression: str
    params: dict | None = None
    is_enabled: bool
    temporal_schedule_id: str | None = None
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

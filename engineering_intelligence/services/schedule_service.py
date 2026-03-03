"""Scheduled workflow service — manages cron-based Temporal schedules."""

from temporalio.client import Schedule, ScheduleActionStartWorkflow, ScheduleSpec

from engineering_intelligence.config import get_settings
from engineering_intelligence.schemas.schedule import resolve_cron
from engineering_intelligence.workflows.dispatch import (
    _WORKFLOW_MAP,
    _build_workflow_args,
    get_temporal_client,
)


async def create_temporal_schedule(
    schedule_name: str,
    workflow_type: str,
    cron_expression: str,
    params: dict | None = None,
) -> str:
    """Create a cron schedule in Temporal and return the schedule ID.

    Uses Temporal's native schedule support so the server handles
    timing, retries, and overlap policies.
    """
    settings = get_settings()
    client = await get_temporal_client()

    cron = resolve_cron(cron_expression)
    workflow_class = _WORKFLOW_MAP.get(workflow_type)
    if not workflow_class:
        raise ValueError(f"Unknown workflow type: {workflow_type}")

    args = _build_workflow_args(workflow_type, params or {})

    schedule_id = f"schedule-{schedule_name}"

    await client.create_schedule(
        schedule_id,
        Schedule(
            action=ScheduleActionStartWorkflow(
                workflow_class,
                arg=args,
                id=f"{schedule_name}-{{{{.ScheduleTime.Format \"20060102T150405\"}}}}",
                task_queue=settings.temporal_task_queue,
            ),
            spec=ScheduleSpec(cron_expressions=[cron]),
        ),
    )

    return schedule_id


async def pause_temporal_schedule(schedule_id: str) -> None:
    """Pause (disable) an existing Temporal schedule."""
    client = await get_temporal_client()
    handle = client.get_schedule_handle(schedule_id)
    await handle.pause(note="Paused by EI Platform")


async def unpause_temporal_schedule(schedule_id: str) -> None:
    """Unpause (re-enable) an existing Temporal schedule."""
    client = await get_temporal_client()
    handle = client.get_schedule_handle(schedule_id)
    await handle.unpause(note="Unpaused by EI Platform")


async def delete_temporal_schedule(schedule_id: str) -> None:
    """Delete a Temporal schedule entirely."""
    client = await get_temporal_client()
    handle = client.get_schedule_handle(schedule_id)
    await handle.delete()


async def trigger_temporal_schedule(schedule_id: str) -> None:
    """Immediately trigger a schedule (run it now, outside its cron window)."""
    client = await get_temporal_client()
    handle = client.get_schedule_handle(schedule_id)
    await handle.trigger()

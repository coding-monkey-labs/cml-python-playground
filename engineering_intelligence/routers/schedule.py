"""Schedule router — manage cron-based workflow schedules."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.auth.dependencies import require_admin
from engineering_intelligence.db import get_db
from engineering_intelligence.db.models import User
from engineering_intelligence.repositories.schedule_repo import ScheduleRepository
from engineering_intelligence.schemas.schedule import (
    CRON_PRESETS,
    ScheduleCreateRequest,
    ScheduleResponse,
    ScheduleUpdateRequest,
    resolve_cron,
)
from engineering_intelligence.services.schedule_service import (
    create_temporal_schedule,
    delete_temporal_schedule,
    pause_temporal_schedule,
    trigger_temporal_schedule,
    unpause_temporal_schedule,
)
from engineering_intelligence.workflows.dispatch import get_supported_workflows

router = APIRouter(prefix="/schedules", tags=["schedules"])


def _to_response(schedule) -> ScheduleResponse:
    data = ScheduleResponse.model_validate(schedule)
    if schedule.params:
        try:
            data.params = json.loads(schedule.params)
        except (json.JSONDecodeError, TypeError):
            data.params = None
    return data


@router.get("/presets")
async def list_presets(
    _user: User = Depends(require_admin),
):
    """List available cron presets."""
    return {"presets": CRON_PRESETS}


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    request: ScheduleCreateRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
):
    """Create a new workflow schedule. Optionally registers with Temporal."""
    supported = get_supported_workflows()
    if request.workflow_type not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow type '{request.workflow_type}'. Supported: {supported}",
        )

    repo = ScheduleRepository(db)
    existing = await repo.get_by_name(request.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Schedule '{request.name}' already exists")

    cron = resolve_cron(request.cron_expression)

    params_json = json.dumps(request.params) if request.params else None
    schedule = await repo.create(
        name=request.name,
        workflow_type=request.workflow_type,
        cron_expression=cron,
        params=params_json,
        is_enabled=request.is_enabled,
    )

    # Register with Temporal if enabled
    temporal_id = None
    if request.is_enabled:
        try:
            temporal_id = await create_temporal_schedule(
                schedule_name=request.name,
                workflow_type=request.workflow_type,
                cron_expression=cron,
                params=request.params,
            )
            await repo.update(schedule.id, temporal_schedule_id=temporal_id)
        except Exception:
            # Temporal may be unavailable — schedule is saved in DB regardless
            pass

    # Re-fetch for updated data
    schedule = await repo.get_by_id(schedule.id)
    return _to_response(schedule)


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
):
    """List all workflow schedules."""
    repo = ScheduleRepository(db)
    schedules = await repo.list_all(enabled_only=enabled_only)
    return [_to_response(s) for s in schedules]


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
):
    """Get a specific schedule by ID."""
    repo = ScheduleRepository(db)
    schedule = await repo.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return _to_response(schedule)


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    request: ScheduleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
):
    """Update a schedule's cron expression, params, or enabled state."""
    repo = ScheduleRepository(db)
    schedule = await repo.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    cron = resolve_cron(request.cron_expression) if request.cron_expression else None
    params_json = json.dumps(request.params) if request.params is not None else None

    updated = await repo.update(
        schedule_id,
        cron_expression=cron,
        params=params_json,
        is_enabled=request.is_enabled,
    )

    # Sync enabled state with Temporal
    if request.is_enabled is not None and schedule.temporal_schedule_id:
        try:
            if request.is_enabled:
                await unpause_temporal_schedule(schedule.temporal_schedule_id)
            else:
                await pause_temporal_schedule(schedule.temporal_schedule_id)
        except Exception:
            pass

    return _to_response(updated)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
):
    """Delete a schedule. Also removes it from Temporal if registered."""
    repo = ScheduleRepository(db)
    schedule = await repo.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Remove from Temporal first
    if schedule.temporal_schedule_id:
        try:
            await delete_temporal_schedule(schedule.temporal_schedule_id)
        except Exception:
            pass

    await repo.delete(schedule_id)


@router.post("/{schedule_id}/trigger", status_code=202)
async def trigger_schedule_now(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
):
    """Immediately trigger a scheduled workflow (outside its cron window)."""
    repo = ScheduleRepository(db)
    schedule = await repo.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if not schedule.temporal_schedule_id:
        raise HTTPException(
            status_code=400,
            detail="Schedule is not registered with Temporal. Enable it first.",
        )

    try:
        await trigger_temporal_schedule(schedule.temporal_schedule_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Temporal trigger failed: {e}")

    return {"message": f"Schedule '{schedule.name}' triggered"}


@router.post("/{schedule_id}/enable", response_model=ScheduleResponse)
async def enable_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
):
    """Enable a schedule and register with Temporal if not yet registered."""
    repo = ScheduleRepository(db)
    schedule = await repo.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    await repo.update(schedule_id, is_enabled=True)

    # Register with Temporal if not yet
    if not schedule.temporal_schedule_id:
        try:
            params = json.loads(schedule.params) if schedule.params else None
            temporal_id = await create_temporal_schedule(
                schedule_name=schedule.name,
                workflow_type=schedule.workflow_type,
                cron_expression=schedule.cron_expression,
                params=params,
            )
            await repo.update(schedule_id, temporal_schedule_id=temporal_id)
        except Exception:
            pass
    else:
        try:
            await unpause_temporal_schedule(schedule.temporal_schedule_id)
        except Exception:
            pass

    schedule = await repo.get_by_id(schedule_id)
    return _to_response(schedule)


@router.post("/{schedule_id}/disable", response_model=ScheduleResponse)
async def disable_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
):
    """Disable a schedule (pauses it in Temporal)."""
    repo = ScheduleRepository(db)
    schedule = await repo.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    await repo.update(schedule_id, is_enabled=False)

    if schedule.temporal_schedule_id:
        try:
            await pause_temporal_schedule(schedule.temporal_schedule_id)
        except Exception:
            pass

    schedule = await repo.get_by_id(schedule_id)
    return _to_response(schedule)

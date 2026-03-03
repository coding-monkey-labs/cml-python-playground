"""Workflow schedule repository."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.db.models import WorkflowSchedule


class ScheduleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        name: str,
        workflow_type: str,
        cron_expression: str,
        params: str | None = None,
        is_enabled: bool = True,
    ) -> WorkflowSchedule:
        schedule = WorkflowSchedule(
            name=name,
            workflow_type=workflow_type,
            cron_expression=cron_expression,
            params=params,
            is_enabled=is_enabled,
        )
        self._db.add(schedule)
        await self._db.flush()
        return schedule

    async def get_by_id(self, schedule_id: int) -> WorkflowSchedule | None:
        result = await self._db.execute(
            select(WorkflowSchedule).where(WorkflowSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> WorkflowSchedule | None:
        result = await self._db.execute(
            select(WorkflowSchedule).where(WorkflowSchedule.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self, enabled_only: bool = False) -> list[WorkflowSchedule]:
        stmt = select(WorkflowSchedule).order_by(WorkflowSchedule.created_at.desc())
        if enabled_only:
            stmt = stmt.where(WorkflowSchedule.is_enabled.is_(True))
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        schedule_id: int,
        cron_expression: str | None = None,
        params: str | None = None,
        is_enabled: bool | None = None,
        temporal_schedule_id: str | None = None,
        last_run_at: datetime | None = None,
        next_run_at: datetime | None = None,
    ) -> WorkflowSchedule | None:
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return None
        if cron_expression is not None:
            schedule.cron_expression = cron_expression
        if params is not None:
            schedule.params = params
        if is_enabled is not None:
            schedule.is_enabled = is_enabled
        if temporal_schedule_id is not None:
            schedule.temporal_schedule_id = temporal_schedule_id
        if last_run_at is not None:
            schedule.last_run_at = last_run_at
        if next_run_at is not None:
            schedule.next_run_at = next_run_at
        await self._db.flush()
        return schedule

    async def delete(self, schedule_id: int) -> bool:
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return False
        await self._db.delete(schedule)
        await self._db.flush()
        return True

    async def count_enabled(self) -> int:
        result = await self._db.execute(
            select(WorkflowSchedule).where(WorkflowSchedule.is_enabled.is_(True))
        )
        return len(result.scalars().all())

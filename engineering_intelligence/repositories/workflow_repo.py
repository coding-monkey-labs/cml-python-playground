"""Workflow run repository."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.db.models import WorkflowRun, WorkflowStatus


class WorkflowRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, workflow_type: str, workflow_id: str,
                     input_params: str | None = None) -> WorkflowRun:
        run = WorkflowRun(
            workflow_type=workflow_type,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            input_params=input_params,
        )
        self._db.add(run)
        await self._db.flush()
        return run

    async def get_by_workflow_id(self, workflow_id: str) -> WorkflowRun | None:
        result = await self._db.execute(
            select(WorkflowRun).where(WorkflowRun.workflow_id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def mark_running(self, workflow_id: str) -> None:
        run = await self.get_by_workflow_id(workflow_id)
        if run:
            run.status = WorkflowStatus.RUNNING
            run.started_at = datetime.now(timezone.utc)
            await self._db.flush()

    async def mark_completed(self, workflow_id: str, result: str | None = None) -> None:
        run = await self.get_by_workflow_id(workflow_id)
        if run:
            run.status = WorkflowStatus.COMPLETED
            run.result = result
            run.completed_at = datetime.now(timezone.utc)
            await self._db.flush()

    async def mark_failed(self, workflow_id: str, error_message: str) -> None:
        run = await self.get_by_workflow_id(workflow_id)
        if run:
            run.status = WorkflowStatus.FAILED
            run.error_message = error_message
            run.completed_at = datetime.now(timezone.utc)
            await self._db.flush()

    async def get_recent(self, limit: int = 20) -> list[WorkflowRun]:
        result = await self._db.execute(
            select(WorkflowRun)
            .order_by(WorkflowRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

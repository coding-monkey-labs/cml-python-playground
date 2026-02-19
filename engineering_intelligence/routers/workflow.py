"""Workflow router — trigger ingestion, rebuilds, view status."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.auth.dependencies import require_admin
from engineering_intelligence.db import get_db
from engineering_intelligence.db.models import User
from engineering_intelligence.repositories.workflow_repo import WorkflowRepository
from engineering_intelligence.schemas.workflow import WorkflowStatusResponse, WorkflowTriggerRequest

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/trigger", response_model=WorkflowStatusResponse, status_code=202)
async def trigger_workflow(
    request: WorkflowTriggerRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
):
    """Trigger a workflow (admin only). Actual Temporal dispatch is in the workflow layer."""
    import uuid

    repo = WorkflowRepository(db)
    workflow_id = f"{request.workflow_type}-{uuid.uuid4().hex[:8]}"
    import json
    run = await repo.create(
        workflow_type=request.workflow_type,
        workflow_id=workflow_id,
        input_params=json.dumps(request.params) if request.params else None,
    )
    # In production, this would dispatch to Temporal here
    return WorkflowStatusResponse.model_validate(run)


@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
):
    repo = WorkflowRepository(db)
    run = await repo.get_by_workflow_id(workflow_id)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return WorkflowStatusResponse.model_validate(run)


@router.get("/recent", response_model=list[WorkflowStatusResponse])
async def get_recent_workflows(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin),
):
    repo = WorkflowRepository(db)
    runs = await repo.get_recent(limit=limit)
    return [WorkflowStatusResponse.model_validate(r) for r in runs]

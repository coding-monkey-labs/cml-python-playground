"""Pipeline CRUD routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.api.middleware.auth import get_current_user, require_admin
from rag_platform.core.exceptions import PipelineError, RAGInstanceNotFoundError
from rag_platform.db.session import get_db
from rag_platform.schemas.pipeline import PipelineCreate, PipelineResponse, PipelineUpdate
from rag_platform.services.pipeline_service import PipelineService

router = APIRouter(prefix="/rag/pipeline", tags=["Pipelines"])


@router.post("", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    data: PipelineCreate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Create a new ingestion pipeline."""
    try:
        service = PipelineService(db)
        pipeline = await service.create(data)
        return pipeline
    except RAGInstanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except PipelineError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message) from e


@router.get("", response_model=list[PipelineResponse])
async def list_pipelines(
    instance_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """List pipelines, optionally filtered by RAG instance."""
    service = PipelineService(db)
    if instance_id:
        return await service.list_by_instance(instance_id)
    return await service.list_all()


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get a pipeline by ID."""
    try:
        service = PipelineService(db)
        return await service.get_by_id(pipeline_id)
    except PipelineError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e


@router.patch("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: uuid.UUID,
    data: PipelineUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Update a pipeline."""
    try:
        service = PipelineService(db)
        return await service.update(pipeline_id, data)
    except PipelineError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Delete a pipeline."""
    try:
        service = PipelineService(db)
        await service.delete(pipeline_id)
    except PipelineError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e


@router.post("/{pipeline_id}/pause", response_model=PipelineResponse)
async def pause_pipeline(
    pipeline_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Pause a pipeline."""
    try:
        service = PipelineService(db)
        return await service.pause(pipeline_id)
    except PipelineError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e


@router.post("/{pipeline_id}/resume", response_model=PipelineResponse)
async def resume_pipeline(
    pipeline_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Resume a paused pipeline."""
    try:
        service = PipelineService(db)
        return await service.resume(pipeline_id)
    except PipelineError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e

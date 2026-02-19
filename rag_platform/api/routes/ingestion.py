"""Ingestion routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.api.middleware.auth import get_current_user
from rag_platform.core.exceptions import IngestionError, RAGInstanceNotFoundError
from rag_platform.db.models.ingestion_job import JobStatus
from rag_platform.db.session import get_db
from rag_platform.schemas.ingestion import (
    DeleteByFilterRequest,
    IngestionJobList,
    IngestionJobResponse,
    IngestRequest,
    ReindexRequest,
)
from rag_platform.services.ingestion_service import IngestionService

router = APIRouter(prefix="/rag", tags=["Ingestion"])


@router.post("/ingest", response_model=IngestionJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_documents(
    request: IngestRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Ingest documents into a RAG instance."""
    try:
        service = IngestionService(db)
        job = await service.ingest(request)
        return job
    except RAGInstanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except IngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        ) from e


@router.post("/reindex", response_model=IngestionJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def reindex(
    request: ReindexRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Trigger a reindex of a RAG instance."""
    try:
        service = IngestionService(db)
        job = await service.reindex(request.rag_instance_id, request.force_full)
        return job
    except RAGInstanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e


@router.post("/delete-by-filter", response_model=IngestionJobResponse)
async def delete_by_filter(
    request: DeleteByFilterRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Delete documents matching a metadata filter."""
    try:
        service = IngestionService(db)
        job = await service.delete_by_filter(request)
        return job
    except RAGInstanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e


@router.get("/ingestion-status", response_model=IngestionJobList)
async def get_ingestion_status(
    instance_id: uuid.UUID | None = Query(None),
    job_status: JobStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get ingestion job status."""
    service = IngestionService(db)
    jobs = await service.get_jobs(
        instance_id=instance_id,
        status=job_status,
        limit=limit,
    )
    return IngestionJobList(items=jobs, total=len(jobs))

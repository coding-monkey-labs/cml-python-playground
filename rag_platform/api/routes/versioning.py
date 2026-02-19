"""Versioning, migration, and federation API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.api.middleware.auth import get_current_user, require_admin
from rag_platform.core.exceptions import RAGInstanceNotFoundError, RAGPlatformError
from rag_platform.db.session import get_db
from rag_platform.schemas.query import QueryResponse
from rag_platform.schemas.versioning import (
    CreateSnapshotRequest,
    FederatedQueryRequest,
    IndexVersionResponse,
    MigrateIndexRequest,
    MigrationJobResponse,
    RollbackRequest,
)
from rag_platform.services.federation_service import FederationService
from rag_platform.services.migration_service import MigrationService
from rag_platform.services.versioning_service import VersioningService

router = APIRouter(prefix="/rag", tags=["Versioning & Migration"])


# ── Version Endpoints ──────────────────────────────────────────────


@router.post(
    "/version/snapshot",
    response_model=IndexVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_snapshot(
    request: CreateSnapshotRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """Create a versioned snapshot of a RAG instance's current state."""
    try:
        service = VersioningService(db)
        version = await service.create_version(
            instance_id=request.rag_instance_id,
            description=request.description,
            created_by=user.get("subject"),
        )
        return version
    except RAGInstanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except RAGPlatformError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        ) from e


@router.get("/version/{instance_id}", response_model=list[IndexVersionResponse])
async def list_versions(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """List all versions for a RAG instance."""
    service = VersioningService(db)
    return await service.list_versions(instance_id)


@router.get(
    "/version/{instance_id}/{version}",
    response_model=IndexVersionResponse,
)
async def get_version(
    instance_id: uuid.UUID,
    version: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get a specific version of a RAG instance."""
    try:
        service = VersioningService(db)
        return await service.get_version(instance_id, version)
    except RAGPlatformError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e


@router.post("/version/rollback")
async def rollback_version(
    request: RollbackRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Roll back a RAG instance to a previous version's configuration."""
    try:
        service = VersioningService(db)
        instance = await service.rollback(
            instance_id=request.rag_instance_id,
            target_version=request.target_version,
        )
        return {
            "message": f"Rolled back to version {request.target_version}",
            "instance_id": str(instance.id),
            "current_version": instance.index_version,
        }
    except RAGPlatformError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e


# ── Migration Endpoints ───────────────────────────────────────────


@router.post(
    "/migrate-index",
    response_model=MigrationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def migrate_index(
    request: MigrateIndexRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Migrate a RAG instance's index from one vector DB to another."""
    try:
        service = MigrationService(db)
        job = await service.create_migration(request)
        return job
    except RAGInstanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except RAGPlatformError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        ) from e


@router.get("/migration/{job_id}", response_model=MigrationJobResponse)
async def get_migration_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get the status of a migration job."""
    try:
        service = MigrationService(db)
        return await service.get_migration(job_id)
    except RAGPlatformError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e


@router.get("/migrations", response_model=list[MigrationJobResponse])
async def list_migrations(
    instance_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """List migration jobs."""
    service = MigrationService(db)
    return await service.list_migrations(instance_id=instance_id, limit=limit)


# ── Federation Endpoints ──────────────────────────────────────────


@router.post("/federated-query", response_model=QueryResponse)
async def federated_query(
    request: FederatedQueryRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Execute a federated query across multiple instances with weighted retrieval."""
    try:
        service = FederationService(db)
        return await service.federated_query(request)
    except RAGPlatformError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        ) from e

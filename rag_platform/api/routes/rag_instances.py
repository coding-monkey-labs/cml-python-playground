"""RAG Instance CRUD routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.api.middleware.auth import get_current_user, require_admin
from rag_platform.core.exceptions import (
    RAGInstanceAlreadyExistsError,
    RAGInstanceNotFoundError,
    RAGPlatformError,
)
from rag_platform.db.session import get_db
from rag_platform.schemas.rag_instance import (
    RAGInstanceCreate,
    RAGInstanceList,
    RAGInstanceResponse,
    RAGInstanceUpdate,
)
from rag_platform.services.rag_instance_service import RAGInstanceService

router = APIRouter(prefix="/rag/instance", tags=["RAG Instances"])


@router.post("", response_model=RAGInstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_instance(
    data: RAGInstanceCreate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Create a new RAG instance."""
    try:
        service = RAGInstanceService(db)
        instance = await service.create(data)
        return instance
    except RAGInstanceAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message) from e
    except RAGPlatformError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        ) from e


@router.get("", response_model=RAGInstanceList)
async def list_instances(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """List all RAG instances."""
    service = RAGInstanceService(db)
    instances = await service.list_all(active_only=active_only)
    return RAGInstanceList(items=instances, total=len(instances))


@router.get("/{instance_id}", response_model=RAGInstanceResponse)
async def get_instance(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get a RAG instance by ID."""
    try:
        service = RAGInstanceService(db)
        return await service.get_by_id(instance_id)
    except RAGInstanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e


@router.patch("/{instance_id}", response_model=RAGInstanceResponse)
async def update_instance(
    instance_id: uuid.UUID,
    data: RAGInstanceUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Update a RAG instance."""
    try:
        service = RAGInstanceService(db)
        return await service.update(instance_id, data)
    except RAGInstanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e


@router.delete("/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_instance(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Delete a RAG instance and its vector DB collection."""
    try:
        service = RAGInstanceService(db)
        await service.delete(instance_id)
    except RAGInstanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e

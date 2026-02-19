"""Query routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.api.middleware.auth import get_current_user
from rag_platform.core.exceptions import RAGInstanceNotFoundError, RAGPlatformError
from rag_platform.db.session import get_db
from rag_platform.schemas.query import (
    CrossInstanceQueryRequest,
    HybridQueryRequest,
    QueryRequest,
    QueryResponse,
)
from rag_platform.services.query_service import QueryService

router = APIRouter(prefix="/rag", tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def semantic_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Execute a semantic query against a RAG instance."""
    try:
        service = QueryService(db)
        return await service.query(request)
    except RAGInstanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except RAGPlatformError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        ) from e


@router.post("/hybrid-query", response_model=QueryResponse)
async def hybrid_query(
    request: HybridQueryRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Execute a hybrid (keyword + semantic) query.

    Phase 1: Falls back to pure semantic search.
    Full hybrid search will be implemented in Phase 4.
    """
    try:
        service = QueryService(db)
        # Phase 1: Convert to semantic query
        semantic_request = QueryRequest(
            rag_instance_id=request.rag_instance_id,
            query=request.query,
            top_k=request.top_k,
            metadata_filter=request.metadata_filter,
        )
        return await service.query(semantic_request)
    except RAGInstanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except RAGPlatformError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        ) from e


@router.post("/cross-instance-query", response_model=QueryResponse)
async def cross_instance_query(
    request: CrossInstanceQueryRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Execute a query across multiple RAG instances."""
    try:
        service = QueryService(db)
        return await service.cross_instance_query(request)
    except RAGPlatformError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        ) from e

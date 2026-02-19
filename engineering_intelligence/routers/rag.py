"""RAG router — similarity search, duplicate check, defect summary."""

from fastapi import APIRouter, Depends

from engineering_intelligence.auth.dependencies import get_current_user
from engineering_intelligence.db.models import User
from engineering_intelligence.schemas.rag import (
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    SimilarityQueryRequest,
    SimilarityQueryResponse,
)
from engineering_intelligence.vector import get_vector_store
from engineering_intelligence.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])


def _get_service() -> RAGService:
    return RAGService(get_vector_store())


@router.post("/similarity", response_model=SimilarityQueryResponse)
async def similarity_search(
    request: SimilarityQueryRequest,
    _user: User = Depends(get_current_user),
):
    service = _get_service()
    return await service.similarity_search(request)


@router.post("/duplicate-check", response_model=DuplicateCheckResponse)
async def check_duplicates(
    request: DuplicateCheckRequest,
    _user: User = Depends(get_current_user),
):
    service = _get_service()
    return await service.check_duplicates(request)


@router.get("/stats")
async def get_rag_stats(
    _user: User = Depends(get_current_user),
):
    service = _get_service()
    return {"document_count": service.get_document_count()}

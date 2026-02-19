"""Agent router — context, risk, duplicate check, review context for AI coding agents."""

from fastapi import APIRouter, Depends

from engineering_intelligence.auth.dependencies import get_current_user
from engineering_intelligence.db.models import User
from engineering_intelligence.graph import get_graph_client, GraphRepository
from engineering_intelligence.schemas.agent import (
    AgentContextRequest,
    AgentContextResponse,
    AgentDuplicateCheckRequest,
    AgentDuplicateCheckResponse,
    AgentReviewContextRequest,
    AgentReviewContextResponse,
    AgentRiskRequest,
    AgentRiskResponse,
)
from engineering_intelligence.services.agent_service import AgentService
from engineering_intelligence.services.rag_service import RAGService
from engineering_intelligence.vector import get_vector_store

router = APIRouter(prefix="/agent", tags=["agent"])


def _get_service() -> AgentService:
    try:
        graph_client = get_graph_client()
        graph_repo = GraphRepository(graph_client)
    except Exception:
        graph_repo = None
    try:
        rag_service = RAGService(get_vector_store())
    except Exception:
        rag_service = None
    return AgentService(graph_repo=graph_repo, rag_service=rag_service)


@router.post("/context", response_model=AgentContextResponse)
async def get_context(
    request: AgentContextRequest,
    _user: User = Depends(get_current_user),
):
    service = _get_service()
    return await service.get_context(request)


@router.post("/risk", response_model=AgentRiskResponse)
async def get_risk(
    request: AgentRiskRequest,
    _user: User = Depends(get_current_user),
):
    service = _get_service()
    return await service.get_risk(request)


@router.post("/duplicate-check", response_model=AgentDuplicateCheckResponse)
async def check_duplicate(
    request: AgentDuplicateCheckRequest,
    _user: User = Depends(get_current_user),
):
    service = _get_service()
    return await service.check_duplicate(request)


@router.post("/review-context", response_model=AgentReviewContextResponse)
async def get_review_context(
    request: AgentReviewContextRequest,
    _user: User = Depends(get_current_user),
):
    service = _get_service()
    return await service.get_review_context(request)

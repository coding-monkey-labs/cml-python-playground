"""Jira router — search, get by ID, similarity search, graph subtree."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.auth.dependencies import get_current_user
from engineering_intelligence.db import get_db
from engineering_intelligence.db.models import User
from engineering_intelligence.graph import get_graph_client, GraphRepository
from engineering_intelligence.repositories.jira_repo import JiraRepository
from engineering_intelligence.schemas.jira import (
    JiraIssueCreate,
    JiraIssueResponse,
    JiraSearchRequest,
)
from engineering_intelligence.services.jira_service import JiraService

router = APIRouter(prefix="/jira", tags=["jira"])


def _get_service(db: AsyncSession) -> JiraService:
    jira_repo = JiraRepository(db)
    try:
        graph_client = get_graph_client()
        graph_repo = GraphRepository(graph_client)
    except Exception:
        graph_repo = None
    return JiraService(jira_repo, graph_repo)


@router.post("/search", response_model=list[JiraIssueResponse])
async def search_jira(
    request: JiraSearchRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    return await service.search(request)


@router.get("/{jira_key}", response_model=JiraIssueResponse)
async def get_jira(
    jira_key: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    issue = await service.get_issue(jira_key)
    if not issue:
        raise HTTPException(status_code=404, detail="Jira issue not found")
    return issue


@router.get("/{root_key}/subtree")
async def get_jira_subtree(
    root_key: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    return await service.get_subtree(root_key)


@router.post("/", response_model=JiraIssueResponse, status_code=201)
async def create_jira_issue(
    data: JiraIssueCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    return await service.upsert_issue(data)

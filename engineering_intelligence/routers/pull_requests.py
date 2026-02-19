"""Pull requests router — search, get, mappings."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.auth.dependencies import get_current_user
from engineering_intelligence.db import get_db
from engineering_intelligence.db.models import User
from engineering_intelligence.graph import get_graph_client, GraphRepository
from engineering_intelligence.repositories.jira_repo import JiraRepository
from engineering_intelligence.repositories.pr_repo import PRRepository
from engineering_intelligence.schemas.pull_requests import PRCreate, PRImpact, PRResponse
from engineering_intelligence.services.pr_service import PRService

router = APIRouter(prefix="/pr", tags=["pull_requests"])


def _get_service(db: AsyncSession) -> PRService:
    pr_repo = PRRepository(db)
    jira_repo = JiraRepository(db)
    try:
        graph_client = get_graph_client()
        graph_repo = GraphRepository(graph_client)
    except Exception:
        graph_repo = None
    return PRService(pr_repo, jira_repo, graph_repo)


@router.get("/search", response_model=list[PRResponse])
async def search_prs(
    query: str | None = None,
    repo: str | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    return await service.search(query=query, repo=repo, limit=limit)


@router.get("/{repo}/{pr_number}", response_model=PRResponse)
async def get_pr(
    repo: str,
    pr_number: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    pr = await service.get_pr(pr_number, repo)
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")
    return pr


@router.get("/{repo}/{pr_number}/impact", response_model=PRImpact)
async def get_pr_impact(
    repo: str,
    pr_number: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    impact = await service.get_impact(pr_number, repo)
    if not impact:
        raise HTTPException(status_code=404, detail="PR not found")
    return impact


@router.post("/", response_model=PRResponse, status_code=201)
async def create_pr(
    data: PRCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    return await service.upsert_pr(data)

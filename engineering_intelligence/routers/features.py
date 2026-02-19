"""Features router — feature tree, metrics, defect density."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.auth.dependencies import get_current_user
from engineering_intelligence.db import get_db
from engineering_intelligence.db.models import User
from engineering_intelligence.graph import get_graph_client, GraphRepository
from engineering_intelligence.repositories.feature_repo import FeatureRepository
from engineering_intelligence.schemas.features import (
    FeatureCreate,
    FeatureMetrics,
    FeatureResponse,
    FeatureTreeNode,
)
from engineering_intelligence.services.feature_service import FeatureService

router = APIRouter(prefix="/features", tags=["features"])


def _get_service(db: AsyncSession) -> FeatureService:
    feature_repo = FeatureRepository(db)
    try:
        graph_client = get_graph_client()
        graph_repo = GraphRepository(graph_client)
    except Exception:
        graph_repo = None
    return FeatureService(feature_repo, graph_repo)


@router.get("/tree", response_model=list[FeatureTreeNode])
async def get_feature_tree(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    return await service.get_feature_tree()


@router.get("/{feature_name}/metrics", response_model=FeatureMetrics)
async def get_feature_metrics(
    feature_name: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    metrics = await service.get_feature_metrics(feature_name)
    if not metrics:
        raise HTTPException(status_code=404, detail="Feature not found")
    return metrics


@router.get("/{feature_name}/defect-density")
async def get_defect_density(
    feature_name: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    density = await service.get_defect_density(feature_name)
    return {"feature_name": feature_name, "defect_density": density}


@router.post("/", response_model=FeatureResponse, status_code=201)
async def create_feature(
    data: FeatureCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = _get_service(db)
    return await service.create_feature(data)

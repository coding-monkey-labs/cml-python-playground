"""Analytics router — hotspots, reopen patterns, developer metrics, feature health."""

from fastapi import APIRouter, Depends

from engineering_intelligence.auth.dependencies import get_current_user, require_admin
from engineering_intelligence.db.models import User
from engineering_intelligence.graph import get_graph_client, GraphRepository
from engineering_intelligence.schemas.analytics import (
    DeveloperMetrics,
    FeatureHealthScore,
    HotspotFeature,
    ReopenPattern,
)
from engineering_intelligence.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _get_service() -> AnalyticsService:
    try:
        graph_client = get_graph_client()
        graph_repo = GraphRepository(graph_client)
    except Exception:
        graph_repo = None
    return AnalyticsService(graph_repo=graph_repo)


@router.get("/hotspots", response_model=list[HotspotFeature])
async def get_hotspot_features(
    limit: int = 10,
    _user: User = Depends(get_current_user),
):
    service = _get_service()
    return await service.get_hotspot_features(limit=limit)


@router.get("/reopen-patterns", response_model=list[ReopenPattern])
async def get_reopen_patterns(
    limit: int = 10,
    _user: User = Depends(get_current_user),
):
    service = _get_service()
    return await service.get_reopen_patterns(limit=limit)


@router.get("/developer/{email}", response_model=DeveloperMetrics)
async def get_developer_metrics(
    email: str,
    _user: User = Depends(get_current_user),
):
    service = _get_service()
    return await service.get_developer_metrics(email)


@router.get("/feature-health/{feature_name}", response_model=FeatureHealthScore)
async def get_feature_health(
    feature_name: str,
    _user: User = Depends(get_current_user),
):
    service = _get_service()
    return await service.get_feature_health(feature_name)

"""Dashboard router — aggregated views for frontend consumption."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.auth.dependencies import get_current_user
from engineering_intelligence.db import get_db
from engineering_intelligence.db.models import User
from engineering_intelligence.schemas.dashboard import (
    ActivityItem,
    DashboardSummary,
    DefectTrends,
    SystemHealth,
)
from engineering_intelligence.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Full dashboard summary: entity counts, workflow status, top hotspots, recent defects."""
    service = DashboardService(db)
    return await service.get_summary()


@router.get("/trends", response_model=DefectTrends)
async def get_defect_trends(
    periods: int = 6,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Defect trends over recent periods (created, resolved, reopened)."""
    service = DashboardService(db)
    return await service.get_defect_trends(periods=periods)


@router.get("/activity", response_model=list[ActivityItem])
async def get_recent_activity(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Combined activity feed from Jira issues, PRs, and workflow runs."""
    service = DashboardService(db)
    return await service.get_recent_activity(limit=limit)


@router.get("/system-health", response_model=SystemHealth)
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """System health check: service status, workflow failure rates."""
    service = DashboardService(db)
    return await service.get_system_health()

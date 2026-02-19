"""Admin UI routes using Jinja2 templates."""

import os

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.db.models.ingestion_job import IngestionJob, JobStatus
from rag_platform.db.models.rag_instance import RAGInstance
from rag_platform.db.session import get_db

router = APIRouter(tags=["UI"])

template_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/")
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Admin dashboard showing platform overview."""
    # Gather stats
    instance_result = await db.execute(select(RAGInstance).order_by(RAGInstance.created_at.desc()))
    instances = list(instance_result.scalars().all())

    active_count = sum(1 for i in instances if i.is_active)
    total_docs = sum(i.document_count for i in instances)

    failed_result = await db.execute(
        select(func.count(IngestionJob.id)).where(IngestionJob.status == JobStatus.FAILED)
    )
    failed_jobs = failed_result.scalar() or 0

    recent_jobs_result = await db.execute(
        select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(10)
    )
    recent_jobs = list(recent_jobs_result.scalars().all())

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "instances": instances,
            "active_count": active_count,
            "total_instances": len(instances),
            "total_documents": total_docs,
            "failed_jobs": failed_jobs,
            "recent_jobs": recent_jobs,
        },
    )

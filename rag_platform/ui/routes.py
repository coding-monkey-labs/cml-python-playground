"""Admin UI routes using Jinja2 templates."""

import os

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.core.config import VectorDBType
from rag_platform.db.models.ingestion_job import IngestionJob, JobStatus
from rag_platform.db.models.migration_job import MigrationJob
from rag_platform.db.models.pipeline import Pipeline
from rag_platform.db.models.rag_instance import RAGInstance
from rag_platform.db.session import get_db
from rag_platform.vectordb.factory import get_vector_db_adapter

router = APIRouter(tags=["UI"])

template_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/")
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Admin dashboard showing platform overview."""
    # Gather instance stats
    instance_result = await db.execute(select(RAGInstance).order_by(RAGInstance.created_at.desc()))
    instances = list(instance_result.scalars().all())

    active_count = sum(1 for i in instances if i.is_active)
    total_docs = sum(i.document_count for i in instances)

    # Failed jobs
    failed_result = await db.execute(
        select(func.count(IngestionJob.id)).where(IngestionJob.status == JobStatus.FAILED)
    )
    failed_jobs = failed_result.scalar() or 0

    # Recent jobs
    recent_jobs_result = await db.execute(
        select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(10)
    )
    recent_jobs = list(recent_jobs_result.scalars().all())

    # Pipeline count
    pipeline_result = await db.execute(select(func.count(Pipeline.id)))
    total_pipelines = pipeline_result.scalar() or 0

    # Vector DB health
    db_health = {}
    for db_type in VectorDBType:
        try:
            adapter = get_vector_db_adapter(db_type)
            health = await adapter.health_check()
            db_health[db_type.value] = health.get("status", "unknown")
        except Exception:
            db_health[db_type.value] = "unavailable"

    # Per-DB instance counts
    db_instance_counts = {}
    for db_type in VectorDBType:
        count = sum(1 for i in instances if i.vector_db_type == db_type)
        db_instance_counts[db_type.value] = count

    # Recent migrations
    migration_result = await db.execute(
        select(MigrationJob).order_by(MigrationJob.created_at.desc()).limit(5)
    )
    recent_migrations = list(migration_result.scalars().all())

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "instances": instances,
            "active_count": active_count,
            "total_instances": len(instances),
            "total_documents": total_docs,
            "total_pipelines": total_pipelines,
            "failed_jobs": failed_jobs,
            "recent_jobs": recent_jobs,
            "db_health": db_health,
            "db_instance_counts": db_instance_counts,
            "recent_migrations": recent_migrations,
        },
    )

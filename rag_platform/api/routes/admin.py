"""Admin routes - metrics, health checks, multi-DB comparison."""

import time

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.api.middleware.auth import require_admin
from rag_platform.core.config import VectorDBType, get_settings
from rag_platform.db.models.ingestion_job import IngestionJob, JobStatus
from rag_platform.db.models.pipeline import Pipeline
from rag_platform.db.models.rag_instance import RAGInstance
from rag_platform.db.session import get_db
from rag_platform.vectordb.factory import get_vector_db_adapter

router = APIRouter(prefix="/rag", tags=["Admin"])
settings = get_settings()


@router.get("/metrics")
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Get platform metrics."""
    # Instance counts
    instance_result = await db.execute(select(func.count(RAGInstance.id)))
    total_instances = instance_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(RAGInstance.id)).where(RAGInstance.is_active.is_(True))
    )
    active_instances = active_result.scalar() or 0

    # Document counts
    doc_result = await db.execute(select(func.sum(RAGInstance.document_count)))
    total_documents = doc_result.scalar() or 0

    # Job counts
    failed_result = await db.execute(
        select(func.count(IngestionJob.id)).where(IngestionJob.status == JobStatus.FAILED)
    )
    failed_jobs = failed_result.scalar() or 0

    running_result = await db.execute(
        select(func.count(IngestionJob.id)).where(IngestionJob.status == JobStatus.RUNNING)
    )
    running_jobs = running_result.scalar() or 0

    # Pipeline counts
    pipeline_result = await db.execute(select(func.count(Pipeline.id)))
    total_pipelines = pipeline_result.scalar() or 0

    # Per-DB instance breakdown
    db_breakdown = {}
    for db_type in VectorDBType:
        count_result = await db.execute(
            select(func.count(RAGInstance.id)).where(
                RAGInstance.vector_db_type == db_type
            )
        )
        db_breakdown[db_type.value] = count_result.scalar() or 0

    return {
        "instances": {
            "total": total_instances,
            "active": active_instances,
            "by_database": db_breakdown,
        },
        "documents": {
            "total": total_documents,
        },
        "pipelines": {
            "total": total_pipelines,
        },
        "jobs": {
            "running": running_jobs,
            "failed": failed_jobs,
        },
    }


@router.get("/vector-db-health")
async def vector_db_health(
    _user: dict = Depends(require_admin),
):
    """Check health of all configured vector databases."""
    health_results = {}

    for db_type in VectorDBType:
        try:
            adapter = get_vector_db_adapter(db_type)
            health_results[db_type.value] = await adapter.health_check()
        except Exception as e:
            health_results[db_type.value] = {"status": "error", "error": str(e)}

    return health_results


@router.get("/vector-db-comparison")
async def vector_db_comparison(
    _user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Compare vector database backends - health, latency, instance counts."""
    comparison = {}

    for db_type in VectorDBType:
        entry: dict = {"type": db_type.value}

        # Health check with latency measurement
        try:
            adapter = get_vector_db_adapter(db_type)
            start = time.monotonic()
            health = await adapter.health_check()
            latency_ms = round((time.monotonic() - start) * 1000, 2)

            entry["status"] = health.get("status", "unknown")
            entry["health_latency_ms"] = latency_ms
            entry["details"] = {k: v for k, v in health.items() if k != "status"}
        except Exception as e:
            entry["status"] = "unavailable"
            entry["health_latency_ms"] = None
            entry["details"] = {"error": str(e)}

        # Instance count on this DB type
        count_result = await db.execute(
            select(func.count(RAGInstance.id)).where(
                RAGInstance.vector_db_type == db_type
            )
        )
        entry["instance_count"] = count_result.scalar() or 0

        # Document count on this DB type
        doc_result = await db.execute(
            select(func.sum(RAGInstance.document_count)).where(
                RAGInstance.vector_db_type == db_type
            )
        )
        entry["document_count"] = doc_result.scalar() or 0

        comparison[db_type.value] = entry

    return comparison

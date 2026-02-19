"""Admin routes - metrics, health checks."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.api.middleware.auth import require_admin
from rag_platform.core.config import VectorDBType, get_settings
from rag_platform.db.models.ingestion_job import IngestionJob, JobStatus
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

    return {
        "instances": {
            "total": total_instances,
            "active": active_instances,
        },
        "documents": {
            "total": total_documents,
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

    # Phase 1: Only Qdrant
    try:
        adapter = get_vector_db_adapter(VectorDBType.QDRANT)
        health_results["qdrant"] = await adapter.health_check()
    except Exception as e:
        health_results["qdrant"] = {"status": "error", "error": str(e)}

    return health_results

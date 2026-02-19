"""Service layer for document ingestion operations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.core.exceptions import IngestionError, RAGInstanceNotFoundError
from rag_platform.core.logging import get_logger
from rag_platform.db.models.ingestion_job import IngestionJob, JobStatus, JobType
from rag_platform.db.models.rag_instance import RAGInstance
from rag_platform.orchestrator.engine import RAGOrchestrator
from rag_platform.schemas.ingestion import DeleteByFilterRequest, IngestRequest
from rag_platform.vectordb.factory import get_vector_db_adapter

logger = get_logger(__name__)


class IngestionService:
    """Business logic for document ingestion and index management."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def _get_instance(self, instance_id: uuid.UUID) -> RAGInstance:
        """Fetch and validate a RAG instance exists and is active."""
        result = await self._db.execute(
            select(RAGInstance).where(RAGInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        if not instance:
            raise RAGInstanceNotFoundError(
                f"RAG instance '{instance_id}' not found"
            )
        if not instance.is_active:
            raise IngestionError(
                f"RAG instance '{instance.name}' is not active",
                details={"instance_id": str(instance_id)},
            )
        return instance

    async def ingest(self, request: IngestRequest) -> IngestionJob:
        """Ingest documents into a RAG instance."""
        instance = await self._get_instance(request.rag_instance_id)

        # Create job record
        job = IngestionJob(
            rag_instance_id=instance.id,
            pipeline_id=request.pipeline_id,
            job_type=JobType.INGEST,
            status=JobStatus.RUNNING,
            total_documents=len(request.documents),
            started_at=datetime.now(timezone.utc),
            triggered_by="api",
        )
        self._db.add(job)
        await self._db.flush()

        try:
            adapter = get_vector_db_adapter(instance.vector_db_type)
            orchestrator = RAGOrchestrator(adapter)

            docs = [
                {
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "doc_id": doc.doc_id,
                }
                for doc in request.documents
            ]

            result = await orchestrator.ingest_documents(
                collection_name=instance.namespace,
                documents=docs,
                embedding_model=instance.embedding_model,
                chunk_size=instance.chunk_size,
                chunk_overlap=instance.chunk_overlap,
                dimension=instance.embedding_dimension,
            )

            # Update job
            job.status = JobStatus.COMPLETED
            job.processed_documents = result["inserted"]
            job.completed_at = datetime.now(timezone.utc)

            # Update instance stats
            instance.document_count += result["inserted"]
            instance.last_sync_at = datetime.now(timezone.utc)

            await self._db.flush()
            logger.info(
                "Ingestion completed",
                instance=instance.name,
                job_id=str(job.id),
                inserted=result["inserted"],
            )
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await self._db.flush()
            raise IngestionError(f"Ingestion failed: {e}") from e

        return job

    async def delete_by_filter(self, request: DeleteByFilterRequest) -> IngestionJob:
        """Delete documents matching a metadata filter."""
        instance = await self._get_instance(request.rag_instance_id)

        job = IngestionJob(
            rag_instance_id=instance.id,
            job_type=JobType.DELETE,
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            triggered_by="api",
            job_metadata={"filter": request.metadata_filter},
        )
        self._db.add(job)
        await self._db.flush()

        try:
            adapter = get_vector_db_adapter(instance.vector_db_type)
            orchestrator = RAGOrchestrator(adapter)

            deleted_count = await orchestrator.delete_by_metadata(
                instance.namespace, request.metadata_filter
            )

            job.status = JobStatus.COMPLETED
            job.processed_documents = deleted_count
            job.completed_at = datetime.now(timezone.utc)

            instance.document_count = max(0, instance.document_count - deleted_count)
            await self._db.flush()

            logger.info(
                "Delete by filter completed",
                instance=instance.name,
                deleted=deleted_count,
            )
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await self._db.flush()
            raise

        return job

    async def reindex(self, instance_id: uuid.UUID, force_full: bool = False) -> IngestionJob:
        """Trigger a reindex of a RAG instance."""
        instance = await self._get_instance(instance_id)

        job = IngestionJob(
            rag_instance_id=instance.id,
            job_type=JobType.REINDEX,
            status=JobStatus.PENDING,
            started_at=datetime.now(timezone.utc),
            triggered_by="api",
            job_metadata={"force_full": force_full},
        )
        self._db.add(job)
        await self._db.flush()

        logger.info(
            "Reindex job created",
            instance=instance.name,
            job_id=str(job.id),
            force_full=force_full,
        )
        return job

    async def get_jobs(
        self,
        instance_id: uuid.UUID | None = None,
        status: JobStatus | None = None,
        limit: int = 50,
    ) -> list[IngestionJob]:
        """List ingestion jobs with optional filters."""
        query = select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(limit)
        if instance_id:
            query = query.where(IngestionJob.rag_instance_id == instance_id)
        if status:
            query = query.where(IngestionJob.status == status)
        result = await self._db.execute(query)
        return list(result.scalars().all())

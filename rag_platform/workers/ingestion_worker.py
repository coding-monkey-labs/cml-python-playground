"""Background ingestion worker for async document processing."""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from rag_platform.core.config import get_settings
from rag_platform.core.logging import get_logger
from rag_platform.db.models.ingestion_job import IngestionJob, JobStatus, JobType
from rag_platform.db.session import async_session_factory

logger = get_logger(__name__)
settings = get_settings()


class IngestionWorker:
    """Background worker that processes pending ingestion jobs.

    Polls for pending reindex jobs and processes them asynchronously.
    Direct ingest/delete operations are handled synchronously in the API
    for Phase 1; this worker handles deferred jobs like reindex.
    """

    def __init__(self, poll_interval: float = 10.0):
        self._poll_interval = poll_interval
        self._running = False

    async def start(self) -> None:
        """Start the worker loop."""
        self._running = True
        logger.info("Ingestion worker started", poll_interval=self._poll_interval)

        while self._running:
            try:
                await self._process_pending_jobs()
            except Exception:
                logger.exception("Error in ingestion worker loop")
            await asyncio.sleep(self._poll_interval)

    async def stop(self) -> None:
        """Stop the worker loop."""
        self._running = False
        logger.info("Ingestion worker stopped")

    async def _process_pending_jobs(self) -> None:
        """Find and process pending jobs."""
        async with async_session_factory() as db:
            result = await db.execute(
                select(IngestionJob)
                .where(IngestionJob.status == JobStatus.PENDING)
                .order_by(IngestionJob.created_at.asc())
                .limit(5)
            )
            jobs = list(result.scalars().all())

            for job in jobs:
                await self._process_job(db, job)
                await db.commit()

    async def _process_job(self, db, job: IngestionJob) -> None:
        """Process a single ingestion job."""
        logger.info(
            "Processing job",
            job_id=str(job.id),
            job_type=job.job_type.value,
        )

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        await db.flush()

        try:
            if job.job_type == JobType.REINDEX:
                await self._handle_reindex(db, job)
            else:
                logger.warning("Unknown job type for worker", job_type=job.job_type.value)
                job.status = JobStatus.FAILED
                job.error_message = f"Worker does not handle job type: {job.job_type.value}"
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.retry_count += 1
            logger.exception("Job failed", job_id=str(job.id))

            # Retry with backoff if under max retries
            if job.retry_count < job.max_retries:
                job.status = JobStatus.RETRYING
                logger.info(
                    "Job will be retried",
                    job_id=str(job.id),
                    retry_count=job.retry_count,
                )
                # Reset to pending for next poll cycle
                job.status = JobStatus.PENDING

        job.completed_at = datetime.now(timezone.utc)
        await db.flush()

    async def _handle_reindex(self, db, job: IngestionJob) -> None:
        """Handle a reindex job.

        Phase 1: Simply marks the job as completed.
        Full reindex logic (re-read source, re-chunk, re-embed) requires
        pipeline source configuration which is Phase 2.
        """
        logger.info(
            "Reindex job acknowledged (full reindex in Phase 2)",
            job_id=str(job.id),
            instance_id=str(job.rag_instance_id),
        )
        job.status = JobStatus.COMPLETED

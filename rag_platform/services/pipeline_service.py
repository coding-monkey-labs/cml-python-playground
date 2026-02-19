"""Service layer for Pipeline operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.core.exceptions import PipelineError, RAGInstanceNotFoundError
from rag_platform.core.logging import get_logger
from rag_platform.db.models.pipeline import Pipeline, PipelineStatus
from rag_platform.db.models.rag_instance import RAGInstance
from rag_platform.schemas.pipeline import PipelineCreate, PipelineUpdate

logger = get_logger(__name__)


class PipelineService:
    """Business logic for pipeline CRUD and lifecycle."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, data: PipelineCreate) -> Pipeline:
        """Create a new pipeline attached to a RAG instance."""
        # Verify RAG instance exists
        result = await self._db.execute(
            select(RAGInstance).where(RAGInstance.id == data.rag_instance_id)
        )
        instance = result.scalar_one_or_none()
        if not instance:
            raise RAGInstanceNotFoundError(
                f"RAG instance '{data.rag_instance_id}' not found"
            )

        # Check for duplicate pipeline name within the same instance
        existing = await self._db.execute(
            select(Pipeline).where(
                Pipeline.name == data.name,
                Pipeline.rag_instance_id == data.rag_instance_id,
            )
        )
        if existing.scalar_one_or_none():
            raise PipelineError(
                f"Pipeline '{data.name}' already exists for this RAG instance"
            )

        pipeline = Pipeline(
            name=data.name,
            description=data.description,
            rag_instance_id=data.rag_instance_id,
            source_type=data.source_type,
            source_config=data.source_config,
            transformation_config=data.transformation_config,
            metadata_enrichment_rules=data.metadata_enrichment_rules,
            dedup_enabled=data.dedup_enabled,
            dedup_field=data.dedup_field,
            update_policy=data.update_policy,
            cron_schedule=data.cron_schedule,
            ingestion_frequency_minutes=data.ingestion_frequency_minutes,
        )
        self._db.add(pipeline)
        await self._db.flush()

        logger.info(
            "Created pipeline",
            name=pipeline.name,
            instance=str(data.rag_instance_id),
        )
        return pipeline

    async def get_by_id(self, pipeline_id: uuid.UUID) -> Pipeline:
        """Get a pipeline by ID."""
        result = await self._db.execute(
            select(Pipeline).where(Pipeline.id == pipeline_id)
        )
        pipeline = result.scalar_one_or_none()
        if not pipeline:
            raise PipelineError(f"Pipeline '{pipeline_id}' not found")
        return pipeline

    async def list_by_instance(self, instance_id: uuid.UUID) -> list[Pipeline]:
        """List all pipelines for a RAG instance."""
        result = await self._db.execute(
            select(Pipeline)
            .where(Pipeline.rag_instance_id == instance_id)
            .order_by(Pipeline.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Pipeline]:
        """List all pipelines."""
        result = await self._db.execute(
            select(Pipeline).order_by(Pipeline.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self, pipeline_id: uuid.UUID, data: PipelineUpdate
    ) -> Pipeline:
        """Update a pipeline."""
        pipeline = await self.get_by_id(pipeline_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pipeline, field, value)
        await self._db.flush()
        logger.info("Updated pipeline", name=pipeline.name, id=str(pipeline.id))
        return pipeline

    async def delete(self, pipeline_id: uuid.UUID) -> None:
        """Delete a pipeline."""
        pipeline = await self.get_by_id(pipeline_id)
        await self._db.delete(pipeline)
        await self._db.flush()
        logger.info("Deleted pipeline", name=pipeline.name, id=str(pipeline.id))

    async def pause(self, pipeline_id: uuid.UUID) -> Pipeline:
        """Pause a pipeline."""
        pipeline = await self.get_by_id(pipeline_id)
        pipeline.status = PipelineStatus.PAUSED
        await self._db.flush()
        logger.info("Paused pipeline", name=pipeline.name)
        return pipeline

    async def resume(self, pipeline_id: uuid.UUID) -> Pipeline:
        """Resume a paused pipeline."""
        pipeline = await self.get_by_id(pipeline_id)
        pipeline.status = PipelineStatus.ACTIVE
        await self._db.flush()
        logger.info("Resumed pipeline", name=pipeline.name)
        return pipeline

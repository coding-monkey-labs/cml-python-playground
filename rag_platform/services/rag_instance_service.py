"""Service layer for RAG Instance operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.core.exceptions import (
    RAGInstanceAlreadyExistsError,
    RAGInstanceNotFoundError,
)
from rag_platform.core.logging import get_logger
from rag_platform.db.models.rag_instance import RAGInstance
from rag_platform.orchestrator.engine import RAGOrchestrator
from rag_platform.schemas.rag_instance import RAGInstanceCreate, RAGInstanceUpdate
from rag_platform.vectordb.factory import get_vector_db_adapter

logger = get_logger(__name__)


class RAGInstanceService:
    """Business logic for RAG instance CRUD and lifecycle."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, data: RAGInstanceCreate) -> RAGInstance:
        """Create a new RAG instance and its vector DB collection."""
        # Check for duplicate name
        existing = await self._db.execute(
            select(RAGInstance).where(RAGInstance.name == data.name)
        )
        if existing.scalar_one_or_none():
            raise RAGInstanceAlreadyExistsError(
                f"RAG instance '{data.name}' already exists"
            )

        instance = RAGInstance(
            name=data.name,
            description=data.description,
            vector_db_type=data.vector_db_type,
            namespace=data.namespace,
            embedding_model=data.embedding_model,
            embedding_dimension=data.embedding_dimension,
            chunk_size=data.chunk_size,
            chunk_overlap=data.chunk_overlap,
            metadata_schema=data.metadata_schema,
        )
        self._db.add(instance)
        await self._db.flush()

        # Create the vector DB collection
        adapter = get_vector_db_adapter(instance.vector_db_type)
        orchestrator = RAGOrchestrator(adapter)
        await orchestrator.ensure_collection(instance.namespace, instance.embedding_dimension)

        logger.info("Created RAG instance", name=instance.name, id=str(instance.id))
        return instance

    async def get_by_id(self, instance_id: uuid.UUID) -> RAGInstance:
        """Get a RAG instance by ID."""
        result = await self._db.execute(
            select(RAGInstance).where(RAGInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        if not instance:
            raise RAGInstanceNotFoundError(
                f"RAG instance with ID '{instance_id}' not found"
            )
        return instance

    async def get_by_name(self, name: str) -> RAGInstance:
        """Get a RAG instance by name."""
        result = await self._db.execute(
            select(RAGInstance).where(RAGInstance.name == name)
        )
        instance = result.scalar_one_or_none()
        if not instance:
            raise RAGInstanceNotFoundError(
                f"RAG instance '{name}' not found"
            )
        return instance

    async def list_all(self, active_only: bool = False) -> list[RAGInstance]:
        """List all RAG instances."""
        query = select(RAGInstance).order_by(RAGInstance.created_at.desc())
        if active_only:
            query = query.where(RAGInstance.is_active.is_(True))
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def update(
        self, instance_id: uuid.UUID, data: RAGInstanceUpdate
    ) -> RAGInstance:
        """Update a RAG instance."""
        instance = await self.get_by_id(instance_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(instance, field, value)
        await self._db.flush()
        logger.info("Updated RAG instance", name=instance.name, id=str(instance.id))
        return instance

    async def delete(self, instance_id: uuid.UUID) -> None:
        """Delete a RAG instance and its vector DB collection."""
        instance = await self.get_by_id(instance_id)

        # Delete the vector DB collection
        try:
            adapter = get_vector_db_adapter(instance.vector_db_type)
            orchestrator = RAGOrchestrator(adapter)
            exists = await adapter.collection_exists(instance.namespace)
            if exists:
                await orchestrator.delete_collection(instance.namespace)
        except Exception:
            logger.warning(
                "Failed to delete vector DB collection, proceeding with DB deletion",
                namespace=instance.namespace,
            )

        await self._db.delete(instance)
        await self._db.flush()
        logger.info("Deleted RAG instance", name=instance.name, id=str(instance.id))

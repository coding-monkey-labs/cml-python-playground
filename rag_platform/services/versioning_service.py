"""Service layer for index versioning and snapshot operations."""

import json
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.core.config import get_settings
from rag_platform.core.exceptions import RAGInstanceNotFoundError, RAGPlatformError
from rag_platform.core.logging import get_logger
from rag_platform.db.models.index_version import IndexVersion
from rag_platform.db.models.rag_instance import RAGInstance
from rag_platform.vectordb.factory import get_vector_db_adapter

logger = get_logger(__name__)
settings = get_settings()


class VersioningService:
    """Business logic for index versioning, snapshots, and rollback."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def _get_instance(self, instance_id: uuid.UUID) -> RAGInstance:
        result = await self._db.execute(
            select(RAGInstance).where(RAGInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        if not instance:
            raise RAGInstanceNotFoundError(f"RAG instance '{instance_id}' not found")
        return instance

    async def create_version(
        self,
        instance_id: uuid.UUID,
        description: str | None = None,
        created_by: str | None = None,
    ) -> IndexVersion:
        """Create a new version snapshot of the current index state."""
        instance = await self._get_instance(instance_id)

        # Determine next version number
        latest = await self._db.execute(
            select(IndexVersion)
            .where(IndexVersion.rag_instance_id == instance_id)
            .order_by(IndexVersion.version.desc())
            .limit(1)
        )
        latest_version = latest.scalar_one_or_none()
        next_version = (latest_version.version + 1) if latest_version else 1

        # Build snapshot path
        snapshot_dir = os.path.join(
            settings.raw_document_storage_path, "snapshots", str(instance_id)
        )
        snapshot_path = os.path.join(snapshot_dir, f"v{next_version}.json")

        # Get collection stats from vector DB
        adapter = get_vector_db_adapter(instance.vector_db_type)
        try:
            exists = await adapter.collection_exists(instance.namespace)
            doc_count = await adapter.get_document_count(instance.namespace) if exists else 0
        except Exception:
            doc_count = instance.document_count

        # Create snapshot metadata
        snapshot_metadata = {
            "version": next_version,
            "instance_name": instance.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "config": {
                "embedding_model": instance.embedding_model,
                "embedding_dimension": instance.embedding_dimension,
                "chunk_size": instance.chunk_size,
                "chunk_overlap": instance.chunk_overlap,
                "vector_db_type": instance.vector_db_type.value,
                "namespace": instance.namespace,
            },
            "document_count": doc_count,
        }

        # Save snapshot metadata file
        try:
            os.makedirs(snapshot_dir, exist_ok=True)
            with open(snapshot_path, "w") as f:
                json.dump(snapshot_metadata, f, indent=2)
        except OSError:
            snapshot_path = None  # Non-fatal: continue without file

        # Create version record
        version = IndexVersion(
            rag_instance_id=instance.id,
            version=next_version,
            description=description,
            embedding_model=instance.embedding_model,
            embedding_dimension=instance.embedding_dimension,
            chunk_size=instance.chunk_size,
            chunk_overlap=instance.chunk_overlap,
            vector_db_type=instance.vector_db_type.value,
            namespace=instance.namespace,
            document_count=doc_count,
            snapshot_path=snapshot_path,
            snapshot_metadata=snapshot_metadata,
            created_by=created_by,
        )
        self._db.add(version)

        # Update instance version number
        instance.index_version = next_version
        await self._db.flush()

        logger.info(
            "Created index version",
            instance=instance.name,
            version=next_version,
            documents=doc_count,
        )
        return version

    async def list_versions(self, instance_id: uuid.UUID) -> list[IndexVersion]:
        """List all versions for a RAG instance."""
        result = await self._db.execute(
            select(IndexVersion)
            .where(IndexVersion.rag_instance_id == instance_id)
            .order_by(IndexVersion.version.desc())
        )
        return list(result.scalars().all())

    async def get_version(self, instance_id: uuid.UUID, version: int) -> IndexVersion:
        """Get a specific version."""
        result = await self._db.execute(
            select(IndexVersion).where(
                IndexVersion.rag_instance_id == instance_id,
                IndexVersion.version == version,
            )
        )
        ver = result.scalar_one_or_none()
        if not ver:
            raise RAGPlatformError(
                f"Version {version} not found for instance '{instance_id}'"
            )
        return ver

    async def rollback(
        self,
        instance_id: uuid.UUID,
        target_version: int,
    ) -> RAGInstance:
        """Roll back a RAG instance's configuration to a previous version.

        This restores the embedding model, chunk size, etc. from the snapshot.
        It does NOT restore the actual vector data (that requires re-ingestion
        from the snapshot's source data).
        """
        instance = await self._get_instance(instance_id)
        version = await self.get_version(instance_id, target_version)

        if version.version >= instance.index_version:
            raise RAGPlatformError(
                f"Cannot rollback to version {target_version} — "
                f"current version is {instance.index_version}"
            )

        # Restore configuration
        instance.embedding_model = version.embedding_model
        instance.embedding_dimension = version.embedding_dimension
        instance.chunk_size = version.chunk_size
        instance.chunk_overlap = version.chunk_overlap
        instance.index_version = version.version

        # Create a new version record for the rollback event
        await self.create_version(
            instance_id,
            description=f"Rollback to v{target_version}",
            created_by="system:rollback",
        )

        await self._db.flush()

        logger.info(
            "Rolled back instance",
            instance=instance.name,
            to_version=target_version,
        )
        return instance

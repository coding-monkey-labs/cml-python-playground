"""Index version history ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from rag_platform.db.base import Base


class IndexVersion(Base):
    """Tracks versions of a RAG instance's index configuration and state."""

    __tablename__ = "index_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Parent RAG Instance
    rag_instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rag_instances.id", ondelete="CASCADE"), nullable=False,
        index=True,
    )

    # Version info
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Snapshot of configuration at this version
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_overlap: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_db_type: Mapped[str] = mapped_column(String(50), nullable=False)
    namespace: Mapped[str] = mapped_column(String(255), nullable=False)

    # Stats at version time
    document_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Snapshot metadata
    snapshot_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    snapshot_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Who/what created this version
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<IndexVersion(instance={self.rag_instance_id}, v={self.version})>"

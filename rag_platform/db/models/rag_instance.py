"""RAG Instance ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rag_platform.core.config import VectorDBType
from rag_platform.db.base import Base


class RAGInstance(Base):
    """Represents a logical RAG retrieval space."""

    __tablename__ = "rag_instances"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Vector DB configuration
    vector_db_type: Mapped[VectorDBType] = mapped_column(
        Enum(VectorDBType), nullable=False, default=VectorDBType.QDRANT
    )
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Embedding configuration
    embedding_model: Mapped[str] = mapped_column(
        String(255), nullable=False, default="sentence-transformers/all-MiniLM-L6-v2"
    )
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False, default=384)

    # Chunking configuration
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, default=512)
    chunk_overlap: Mapped[int] = mapped_column(Integer, nullable=False, default=50)

    # Metadata schema (JSON definition of expected metadata fields)
    metadata_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    document_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Versioning
    index_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    embedding_model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    pipelines: Mapped[list["Pipeline"]] = relationship(  # noqa: F821
        "Pipeline", back_populates="rag_instance", cascade="all, delete-orphan"
    )
    ingestion_jobs: Mapped[list["IngestionJob"]] = relationship(  # noqa: F821
        "IngestionJob", back_populates="rag_instance", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RAGInstance(name={self.name!r}, db={self.vector_db_type.value})>"

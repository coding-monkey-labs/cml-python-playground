"""Ingestion job tracking ORM model."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rag_platform.db.base import Base


class JobStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobType(str, PyEnum):
    INGEST = "ingest"
    REINDEX = "reindex"
    DELETE = "delete"
    MIGRATE = "migrate"
    SNAPSHOT = "snapshot"


class IngestionJob(Base):
    """Tracks ingestion and indexing jobs."""

    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Parent RAG Instance
    rag_instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rag_instances.id", ondelete="CASCADE"), nullable=False
    )
    pipeline_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipelines.id", ondelete="SET NULL"), nullable=True
    )

    # Job info
    job_type: Mapped[JobType] = mapped_column(Enum(JobType), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), nullable=False, default=JobStatus.PENDING
    )

    # Progress
    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Retry
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # Metadata
    job_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    triggered_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    rag_instance: Mapped["RAGInstance"] = relationship(  # noqa: F821
        "RAGInstance", back_populates="ingestion_jobs"
    )

    def __repr__(self) -> str:
        return f"<IngestionJob(type={self.job_type.value}, status={self.status.value})>"

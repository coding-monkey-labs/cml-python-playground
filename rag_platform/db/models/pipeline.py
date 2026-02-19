"""Pipeline ORM model."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rag_platform.db.base import Base


class SourceType(str, PyEnum):
    FILE = "file"
    API = "api"
    DATABASE = "database"
    JIRA = "jira"
    GITHUB = "github"
    CONFLUENCE = "confluence"
    CUSTOM = "custom"


class UpdatePolicy(str, PyEnum):
    INCREMENTAL = "incremental"
    FULL = "full"


class PipelineStatus(str, PyEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


class Pipeline(Base):
    """Defines ingestion logic for a RAG instance."""

    __tablename__ = "pipelines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Parent RAG Instance
    rag_instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rag_instances.id", ondelete="CASCADE"), nullable=False
    )

    # Source configuration
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType), nullable=False, default=SourceType.FILE
    )
    source_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Transformation / enrichment
    transformation_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_enrichment_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Deduplication
    dedup_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dedup_field: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Update policy
    update_policy: Mapped[UpdatePolicy] = mapped_column(
        Enum(UpdatePolicy), nullable=False, default=UpdatePolicy.INCREMENTAL
    )

    # Scheduling
    cron_schedule: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ingestion_frequency_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus), nullable=False, default=PipelineStatus.ACTIVE
    )
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_documents_ingested: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    rag_instance: Mapped["RAGInstance"] = relationship(  # noqa: F821
        "RAGInstance", back_populates="pipelines"
    )

    def __repr__(self) -> str:
        return f"<Pipeline(name={self.name!r}, source={self.source_type.value})>"

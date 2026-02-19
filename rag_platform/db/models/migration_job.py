"""Migration job ORM model."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from rag_platform.db.base import Base


class MigrationStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MigrationJob(Base):
    """Tracks index migration jobs between vector databases."""

    __tablename__ = "migration_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Source
    rag_instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rag_instances.id", ondelete="CASCADE"), nullable=False,
    )
    source_db_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_namespace: Mapped[str] = mapped_column(String(255), nullable=False)

    # Target
    target_db_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_namespace: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status
    status: Mapped[MigrationStatus] = mapped_column(
        Enum(MigrationStatus), nullable=False, default=MigrationStatus.PENDING
    )

    # Progress
    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    migrated_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Config
    delete_source_after: Mapped[bool] = mapped_column(default=False, nullable=False)
    update_instance_config: Mapped[bool] = mapped_column(default=True, nullable=False)
    job_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Triggered by
    triggered_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<MigrationJob({self.source_db_type}->{self.target_db_type}, "
            f"status={self.status.value})>"
        )

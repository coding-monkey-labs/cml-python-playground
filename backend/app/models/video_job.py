import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

import enum


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    GENERATING_EDIT_PLAN = "generating_edit_plan"
    EDITING = "editing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(512))
    input_path: Mapped[str] = mapped_column(String(1024))
    output_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.PENDING
    )
    pipeline_type: Mapped[str] = mapped_column(String(128), default="cleaner")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    transcript_chunks = relationship(
        "TranscriptChunk", back_populates="job", cascade="all, delete-orphan"
    )
    edit_plans = relationship(
        "EditPlan", back_populates="job", cascade="all, delete-orphan"
    )

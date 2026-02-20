import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("video_jobs.id", ondelete="CASCADE")
    )
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    word_count: Mapped[int] = mapped_column(default=0)
    is_filler: Mapped[bool] = mapped_column(default=False)

    # Scoring fields
    clarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    engagement_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    filler_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    retention_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    job = relationship("VideoJob", back_populates="transcript_chunks")

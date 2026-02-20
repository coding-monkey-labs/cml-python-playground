import uuid

from pydantic import BaseModel


class TranscriptChunkResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    start_time: float
    end_time: float
    text: str
    confidence: float
    word_count: int
    is_filler: bool
    clarity_score: float | None
    engagement_score: float | None
    filler_score: float | None
    retention_risk_score: float | None

    model_config = {"from_attributes": True}

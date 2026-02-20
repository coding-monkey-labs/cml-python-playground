import uuid
from datetime import datetime

from pydantic import BaseModel


class VideoJobCreate(BaseModel):
    pipeline_type: str = "cleaner"


class VideoJobStatusUpdate(BaseModel):
    status: str
    error_message: str | None = None


class VideoJobResponse(BaseModel):
    id: uuid.UUID
    filename: str
    input_path: str
    output_path: str | None
    audio_path: str | None
    status: str
    pipeline_type: str
    error_message: str | None
    duration_seconds: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VideoJobListResponse(BaseModel):
    jobs: list[VideoJobResponse]
    total: int

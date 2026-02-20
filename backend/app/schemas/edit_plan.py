import uuid
from datetime import datetime

from pydantic import BaseModel


class EditPlanItem(BaseModel):
    start: float
    end: float
    action: str  # remove, compress, flag
    reason: str
    confidence: float = 0.0
    source: str = "local"


class EditPlanResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    start_time: float
    end_time: float
    action: str
    reason: str
    confidence: float
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}

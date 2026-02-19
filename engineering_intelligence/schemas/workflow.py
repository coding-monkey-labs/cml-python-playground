"""Workflow schemas."""

from datetime import datetime

from pydantic import BaseModel


class WorkflowTriggerRequest(BaseModel):
    workflow_type: str
    params: dict | None = None


class WorkflowStatusResponse(BaseModel):
    id: int
    workflow_type: str
    workflow_id: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}

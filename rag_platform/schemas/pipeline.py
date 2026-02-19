"""Pydantic schemas for Pipeline API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from rag_platform.db.models.pipeline import PipelineStatus, SourceType, UpdatePolicy


class PipelineCreate(BaseModel):
    """Schema for creating a new pipeline."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    rag_instance_id: uuid.UUID
    source_type: SourceType = Field(default=SourceType.FILE)
    source_config: dict | None = None
    transformation_config: dict | None = None
    metadata_enrichment_rules: dict | None = None
    dedup_enabled: bool = False
    dedup_field: str | None = None
    update_policy: UpdatePolicy = UpdatePolicy.INCREMENTAL
    cron_schedule: str | None = None
    ingestion_frequency_minutes: int | None = None


class PipelineUpdate(BaseModel):
    """Schema for updating a pipeline."""

    name: str | None = None
    description: str | None = None
    source_config: dict | None = None
    transformation_config: dict | None = None
    metadata_enrichment_rules: dict | None = None
    dedup_enabled: bool | None = None
    dedup_field: str | None = None
    update_policy: UpdatePolicy | None = None
    cron_schedule: str | None = None
    ingestion_frequency_minutes: int | None = None
    status: PipelineStatus | None = None


class PipelineResponse(BaseModel):
    """Schema for pipeline response."""

    id: uuid.UUID
    name: str
    description: str | None
    rag_instance_id: uuid.UUID
    source_type: SourceType
    source_config: dict | None
    transformation_config: dict | None
    metadata_enrichment_rules: dict | None
    dedup_enabled: bool
    dedup_field: str | None
    update_policy: UpdatePolicy
    cron_schedule: str | None
    ingestion_frequency_minutes: int | None
    status: PipelineStatus
    last_run_at: datetime | None
    total_documents_ingested: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

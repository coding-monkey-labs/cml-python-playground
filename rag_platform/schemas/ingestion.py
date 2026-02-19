"""Pydantic schemas for Ingestion API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from rag_platform.db.models.ingestion_job import JobStatus, JobType


class DocumentIngest(BaseModel):
    """Schema for a single document to ingest."""

    content: str = Field(..., min_length=1)
    metadata: dict | None = None
    doc_id: str | None = Field(None, description="External document ID for dedup/update")


class IngestRequest(BaseModel):
    """Schema for ingestion request."""

    rag_instance_id: uuid.UUID
    documents: list[DocumentIngest] = Field(..., min_length=1)
    pipeline_id: uuid.UUID | None = None


class ReindexRequest(BaseModel):
    """Schema for reindex request."""

    rag_instance_id: uuid.UUID
    force_full: bool = False


class DeleteByFilterRequest(BaseModel):
    """Schema for delete-by-filter request."""

    rag_instance_id: uuid.UUID
    metadata_filter: dict = Field(..., description="Metadata filter for selecting documents")


class IngestionJobResponse(BaseModel):
    """Schema for ingestion job status response."""

    id: uuid.UUID
    rag_instance_id: uuid.UUID
    pipeline_id: uuid.UUID | None
    job_type: JobType
    status: JobStatus
    total_documents: int
    processed_documents: int
    failed_documents: int
    error_message: str | None
    retry_count: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestionJobList(BaseModel):
    """Schema for listing ingestion jobs."""

    items: list[IngestionJobResponse]
    total: int

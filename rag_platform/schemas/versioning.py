"""Pydantic schemas for versioning and migration APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from rag_platform.core.config import VectorDBType
from rag_platform.db.models.migration_job import MigrationStatus


# ── Index Version Schemas ──────────────────────────────────────────


class IndexVersionResponse(BaseModel):
    """Schema for index version response."""

    id: uuid.UUID
    rag_instance_id: uuid.UUID
    version: int
    description: str | None
    embedding_model: str
    embedding_dimension: int
    chunk_size: int
    chunk_overlap: int
    vector_db_type: str
    namespace: str
    document_count: int
    snapshot_path: str | None
    created_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateSnapshotRequest(BaseModel):
    """Schema for creating an index snapshot/version."""

    rag_instance_id: uuid.UUID
    description: str | None = None


class RollbackRequest(BaseModel):
    """Schema for rolling back to a previous version."""

    rag_instance_id: uuid.UUID
    target_version: int = Field(..., ge=1)


# ── Migration Schemas ──────────────────────────────────────────────


class MigrateIndexRequest(BaseModel):
    """Schema for migrating an index between vector DBs."""

    rag_instance_id: uuid.UUID
    target_db_type: VectorDBType
    target_namespace: str | None = Field(
        None, description="Target namespace. Defaults to source namespace."
    )
    delete_source_after: bool = False
    update_instance_config: bool = True


class MigrationJobResponse(BaseModel):
    """Schema for migration job response."""

    id: uuid.UUID
    rag_instance_id: uuid.UUID
    source_db_type: str
    source_namespace: str
    target_db_type: str
    target_namespace: str
    status: MigrationStatus
    total_documents: int
    migrated_documents: int
    failed_documents: int
    error_message: str | None
    delete_source_after: bool
    update_instance_config: bool
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Federation Schemas ─────────────────────────────────────────────


class FederatedQueryRequest(BaseModel):
    """Schema for federated query across multiple RAG instances with weights."""

    instance_weights: dict[str, float] = Field(
        ...,
        description="Mapping of instance ID (as string) to weight (0.0-1.0)",
        examples=[{"uuid1": 0.6, "uuid2": 0.4}],
    )
    query: str = Field(..., min_length=1, max_length=10000)
    top_k: int = Field(default=10, ge=1, le=100)
    metadata_filter: dict | None = None
    merge_strategy: str = Field(
        default="weighted_score",
        pattern="^(weighted_score|round_robin|interleave)$",
    )

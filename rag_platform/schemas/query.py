"""Pydantic schemas for Query API."""

import uuid

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Schema for semantic query request."""

    rag_instance_id: uuid.UUID
    query: str = Field(..., min_length=1, max_length=10000)
    top_k: int = Field(default=10, ge=1, le=100)
    metadata_filter: dict | None = None
    include_metadata: bool = True
    include_score: bool = True


class HybridQueryRequest(BaseModel):
    """Schema for hybrid (keyword + semantic) query request."""

    rag_instance_id: uuid.UUID
    query: str = Field(..., min_length=1, max_length=10000)
    top_k: int = Field(default=10, ge=1, le=100)
    metadata_filter: dict | None = None
    semantic_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.3, ge=0.0, le=1.0)


class CrossInstanceQueryRequest(BaseModel):
    """Schema for cross-instance query request."""

    instance_ids: list[uuid.UUID] = Field(..., min_length=1)
    query: str = Field(..., min_length=1, max_length=10000)
    top_k: int = Field(default=10, ge=1, le=100)
    metadata_filter: dict | None = None


class QueryResultItem(BaseModel):
    """Schema for a single query result."""

    content: str
    score: float | None = None
    metadata: dict | None = None
    source_instance: str | None = None


class QueryResponse(BaseModel):
    """Schema for query response."""

    results: list[QueryResultItem]
    total_results: int
    query: str
    rag_instance_id: uuid.UUID | None = None

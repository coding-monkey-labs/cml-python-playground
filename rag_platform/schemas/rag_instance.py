"""Pydantic schemas for RAG Instance API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from rag_platform.core.config import VectorDBType


class RAGInstanceCreate(BaseModel):
    """Schema for creating a new RAG instance."""

    name: str = Field(..., min_length=1, max_length=255, examples=["jira-rag"])
    description: str | None = Field(None, max_length=2000)
    vector_db_type: VectorDBType = Field(default=VectorDBType.QDRANT)
    namespace: str = Field(..., min_length=1, max_length=255, examples=["jira-project-x"])
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dimension: int = Field(default=384, ge=1, le=4096)
    chunk_size: int = Field(default=512, ge=64, le=8192)
    chunk_overlap: int = Field(default=50, ge=0, le=1024)
    metadata_schema: dict | None = None


class RAGInstanceUpdate(BaseModel):
    """Schema for updating a RAG instance."""

    description: str | None = None
    embedding_model: str | None = None
    embedding_dimension: int | None = Field(None, ge=1, le=4096)
    chunk_size: int | None = Field(None, ge=64, le=8192)
    chunk_overlap: int | None = Field(None, ge=0, le=1024)
    metadata_schema: dict | None = None
    is_active: bool | None = None


class RAGInstanceResponse(BaseModel):
    """Schema for RAG instance response."""

    id: uuid.UUID
    name: str
    description: str | None
    vector_db_type: VectorDBType
    namespace: str
    embedding_model: str
    embedding_dimension: int
    chunk_size: int
    chunk_overlap: int
    metadata_schema: dict | None
    is_active: bool
    document_count: int
    last_sync_at: datetime | None
    index_version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RAGInstanceList(BaseModel):
    """Schema for listing RAG instances."""

    items: list[RAGInstanceResponse]
    total: int

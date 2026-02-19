"""Application configuration using pydantic-settings."""

from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorDBType(str, Enum):
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"
    CHROMA = "chroma"
    PGVECTOR = "pgvector"


class EmbeddingModelType(str, Enum):
    HUGGINGFACE = "huggingface"
    SENTENCE_TRANSFORMERS = "sentence-transformers"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RAG_",
        case_sensitive=False,
    )

    # Application
    app_name: str = "RAG Orchestrator Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # API Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # PostgreSQL (metadata store)
    database_url: str = "postgresql+asyncpg://raguser:ragpass@localhost:5432/ragplatform"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # JWT Auth
    jwt_secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    api_key_header: str = "X-API-Key"

    # Default Vector DB
    default_vector_db: VectorDBType = VectorDBType.QDRANT

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_api_key: str | None = None
    qdrant_prefer_grpc: bool = True

    # Weaviate
    weaviate_host: str = "localhost"
    weaviate_port: int = 8080
    weaviate_grpc_port: int = 50051

    # Chroma
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # pgvector (separate from metadata DB)
    pgvector_url: str = "postgresql://raguser:ragpass@localhost:5433/ragvectors"

    # Embedding defaults
    default_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    default_embedding_dimension: int = 384
    default_chunk_size: int = 512
    default_chunk_overlap: int = 50

    # Background workers
    max_ingestion_workers: int = 4
    ingestion_batch_size: int = 100
    max_retries: int = 3
    retry_backoff_base: float = 2.0

    # Query
    default_top_k: int = 10
    query_cache_ttl: int = 300

    # Storage
    raw_document_storage_path: str = "/data/rag-documents"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()

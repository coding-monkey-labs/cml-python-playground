"""Application configuration via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the Engineering Intelligence Platform."""

    # Application
    app_name: str = "Engineering Intelligence Platform"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Auth
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eng_intel"
    database_echo: bool = False

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection: str = "eng_intel_rag"

    # Jira
    jira_base_url: str = "https://jira.example.com"
    jira_api_token: str = ""
    jira_user_email: str = ""

    # GitHub
    github_token: str = ""
    github_org: str = ""
    github_repo: str = ""

    # OpenAI (for embeddings)
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Temporal
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "eng-intel-queue"

    model_config = {"env_prefix": "EI_", "env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

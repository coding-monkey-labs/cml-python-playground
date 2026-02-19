"""Factory for creating Vector DB adapters."""

from rag_platform.core.config import VectorDBType
from rag_platform.core.exceptions import RAGPlatformError
from rag_platform.vectordb.base import VectorDBAdapter


def get_vector_db_adapter(db_type: VectorDBType) -> VectorDBAdapter:
    """Create and return the appropriate VectorDBAdapter for the given type.

    All four vector databases are supported:
    - Qdrant (Phase 1+)
    - Weaviate (Phase 2+)
    - Chroma (Phase 2+)
    - pgvector (Phase 2+)
    """
    if db_type == VectorDBType.QDRANT:
        from rag_platform.vectordb.adapters.qdrant import QdrantAdapter

        return QdrantAdapter()

    if db_type == VectorDBType.WEAVIATE:
        from rag_platform.vectordb.adapters.weaviate import WeaviateAdapter

        return WeaviateAdapter()

    if db_type == VectorDBType.CHROMA:
        from rag_platform.vectordb.adapters.chroma import ChromaAdapter

        return ChromaAdapter()

    if db_type == VectorDBType.PGVECTOR:
        from rag_platform.vectordb.adapters.pgvector import PgvectorAdapter

        return PgvectorAdapter()

    raise RAGPlatformError(f"Unknown vector DB type: {db_type}")

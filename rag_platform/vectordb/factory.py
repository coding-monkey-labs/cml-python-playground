"""Factory for creating Vector DB adapters."""

from rag_platform.core.config import VectorDBType
from rag_platform.core.exceptions import RAGPlatformError
from rag_platform.vectordb.base import VectorDBAdapter


def get_vector_db_adapter(db_type: VectorDBType) -> VectorDBAdapter:
    """Create and return the appropriate VectorDBAdapter for the given type.

    Phase 1: Only Qdrant is supported.
    Phase 2 will add Weaviate, Chroma, pgvector.
    """
    if db_type == VectorDBType.QDRANT:
        from rag_platform.vectordb.adapters.qdrant import QdrantAdapter

        return QdrantAdapter()

    # Phase 2 stubs
    if db_type == VectorDBType.WEAVIATE:
        raise RAGPlatformError(
            f"Vector DB '{db_type.value}' support coming in Phase 2",
            details={"supported": ["qdrant"]},
        )
    if db_type == VectorDBType.CHROMA:
        raise RAGPlatformError(
            f"Vector DB '{db_type.value}' support coming in Phase 2",
            details={"supported": ["qdrant"]},
        )
    if db_type == VectorDBType.PGVECTOR:
        raise RAGPlatformError(
            f"Vector DB '{db_type.value}' support coming in Phase 2",
            details={"supported": ["qdrant"]},
        )

    raise RAGPlatformError(f"Unknown vector DB type: {db_type}")

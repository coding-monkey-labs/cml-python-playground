"""RAG Orchestration Engine - LlamaIndex integration.

This is the core brain of the platform. It handles:
- Document chunking and embedding
- Index creation and management
- Query orchestration
- Multi-index fan-out
"""

import uuid
from typing import Any

from llama_index.core import Document as LlamaDocument
from llama_index.core import Settings as LlamaSettings
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from rag_platform.core.config import get_settings
from rag_platform.core.exceptions import EmbeddingError, IngestionError
from rag_platform.core.logging import get_logger
from rag_platform.vectordb.base import VectorDBAdapter, VectorDocument, VectorSearchResult

logger = get_logger(__name__)


class RAGOrchestrator:
    """Core orchestration engine for RAG operations.

    Manages the lifecycle of documents from ingestion through querying:
    1. Chunk documents using configurable strategies
    2. Generate embeddings via LlamaIndex
    3. Store in vector DB through the adapter abstraction
    4. Query and retrieve relevant documents
    """

    def __init__(self, adapter: VectorDBAdapter):
        self._adapter = adapter
        self._settings = get_settings()
        self._embedding_models: dict[str, HuggingFaceEmbedding] = {}

    def _get_embedding_model(self, model_name: str) -> HuggingFaceEmbedding:
        """Get or create a cached embedding model instance."""
        if model_name not in self._embedding_models:
            try:
                self._embedding_models[model_name] = HuggingFaceEmbedding(
                    model_name=model_name
                )
                logger.info("Loaded embedding model", model=model_name)
            except Exception as e:
                raise EmbeddingError(f"Failed to load embedding model '{model_name}': {e}") from e
        return self._embedding_models[model_name]

    async def ensure_collection(
        self, collection_name: str, dimension: int
    ) -> None:
        """Ensure a vector DB collection exists, creating it if needed."""
        exists = await self._adapter.collection_exists(collection_name)
        if not exists:
            await self._adapter.create_collection(collection_name, dimension)
            logger.info("Created collection", collection=collection_name)

    async def ingest_documents(
        self,
        collection_name: str,
        documents: list[dict[str, Any]],
        embedding_model: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        dimension: int = 384,
    ) -> dict[str, int]:
        """Ingest documents: chunk, embed, and store.

        Args:
            collection_name: Target collection/namespace.
            documents: List of dicts with 'content', optional 'metadata' and 'doc_id'.
            embedding_model: Name of the HuggingFace embedding model.
            chunk_size: Size of text chunks.
            chunk_overlap: Overlap between chunks.
            dimension: Embedding dimension.

        Returns:
            Dict with counts: total_chunks, inserted.
        """
        await self.ensure_collection(collection_name, dimension)

        embed_model = self._get_embedding_model(embedding_model)

        # Build LlamaIndex documents
        llama_docs = []
        for doc in documents:
            metadata = doc.get("metadata", {}) or {}
            if doc.get("doc_id"):
                metadata["doc_id"] = doc["doc_id"]
            llama_docs.append(
                LlamaDocument(text=doc["content"], metadata=metadata)
            )

        # Chunk documents
        splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        nodes = splitter.get_nodes_from_documents(llama_docs)
        logger.info(
            "Chunked documents",
            input_docs=len(documents),
            output_chunks=len(nodes),
            chunk_size=chunk_size,
        )

        if not nodes:
            return {"total_chunks": 0, "inserted": 0}

        # Generate embeddings
        try:
            texts = [node.get_content() for node in nodes]
            embeddings = embed_model.get_text_embedding_batch(texts)
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}") from e

        # Build VectorDocuments
        vector_docs = []
        for i, (node, embedding) in enumerate(zip(nodes, embeddings)):
            doc_id = str(uuid.uuid4())
            node_metadata = node.metadata.copy() if node.metadata else {}
            node_metadata["chunk_index"] = i

            vector_docs.append(
                VectorDocument(
                    id=doc_id,
                    content=node.get_content(),
                    embedding=embedding,
                    metadata=node_metadata,
                )
            )

        # Insert in batches
        batch_size = self._settings.ingestion_batch_size
        total_inserted = 0
        for start in range(0, len(vector_docs), batch_size):
            batch = vector_docs[start : start + batch_size]
            try:
                count = await self._adapter.insert_documents(collection_name, batch)
                total_inserted += count
            except Exception as e:
                raise IngestionError(
                    f"Failed to insert batch starting at index {start}: {e}",
                    details={"batch_start": start, "batch_size": len(batch)},
                ) from e

        logger.info(
            "Ingestion complete",
            collection=collection_name,
            total_chunks=len(vector_docs),
            inserted=total_inserted,
        )
        return {"total_chunks": len(vector_docs), "inserted": total_inserted}

    async def query(
        self,
        collection_name: str,
        query_text: str,
        embedding_model: str,
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Execute a semantic query against a collection.

        Args:
            collection_name: Collection to query.
            query_text: Natural language query.
            embedding_model: Model to use for query embedding.
            top_k: Number of results to return.
            metadata_filter: Optional metadata filter.

        Returns:
            List of VectorSearchResult.
        """
        embed_model = self._get_embedding_model(embedding_model)

        try:
            query_embedding = embed_model.get_query_embedding(query_text)
        except Exception as e:
            raise EmbeddingError(f"Failed to generate query embedding: {e}") from e

        results = await self._adapter.query(
            collection=collection_name,
            query_embedding=query_embedding,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
        logger.info(
            "Query executed",
            collection=collection_name,
            results_count=len(results),
            top_k=top_k,
        )
        return results

    async def delete_by_metadata(
        self, collection_name: str, metadata_filter: dict[str, Any]
    ) -> int:
        """Delete documents matching a metadata filter."""
        count = await self._adapter.delete_by_metadata(collection_name, metadata_filter)
        logger.info(
            "Deleted documents by metadata",
            collection=collection_name,
            filter=metadata_filter,
            count=count,
        )
        return count

    async def delete_collection(self, collection_name: str) -> None:
        """Delete an entire collection."""
        await self._adapter.delete_collection(collection_name)

    async def get_collection_stats(self, collection_name: str) -> dict[str, Any]:
        """Get statistics for a collection."""
        exists = await self._adapter.collection_exists(collection_name)
        if not exists:
            return {"exists": False, "document_count": 0}

        info = await self._adapter.get_collection_info(collection_name)
        return {
            "exists": True,
            "name": info.name,
            "document_count": info.document_count,
            "dimension": info.dimension,
            "metadata": info.metadata,
        }

    async def health_check(self) -> dict[str, Any]:
        """Check health of the underlying vector DB."""
        return await self._adapter.health_check()

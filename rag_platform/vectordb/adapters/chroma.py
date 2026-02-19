"""Chroma vector database adapter."""

from typing import Any

import chromadb

from rag_platform.core.config import get_settings
from rag_platform.core.exceptions import VectorDBConnectionError, VectorDBOperationError
from rag_platform.core.logging import get_logger
from rag_platform.vectordb.base import (
    CollectionInfo,
    VectorDBAdapter,
    VectorDocument,
    VectorSearchResult,
)

logger = get_logger(__name__)


class ChromaAdapter(VectorDBAdapter):
    """Adapter for Chroma vector database."""

    def __init__(self, client: chromadb.ClientAPI | None = None):
        settings = get_settings()
        if client:
            self._client = client
        else:
            self._client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )

    async def create_collection(
        self, name: str, dimension: int, metadata: dict[str, Any] | None = None
    ) -> None:
        try:
            self._client.get_or_create_collection(
                name=name,
                metadata={"dimension": dimension, **(metadata or {})},
            )
            logger.info("Created Chroma collection", collection=name, dimension=dimension)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to create Chroma collection '{name}': {e}"
            ) from e

    async def delete_collection(self, name: str) -> None:
        try:
            self._client.delete_collection(name=name)
            logger.info("Deleted Chroma collection", collection=name)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete Chroma collection '{name}': {e}"
            ) from e

    async def collection_exists(self, name: str) -> bool:
        try:
            collections = self._client.list_collections()
            return name in [c.name for c in collections]
        except Exception as e:
            raise VectorDBConnectionError(
                f"Failed to check Chroma collection existence: {e}"
            ) from e

    async def get_collection_info(self, name: str) -> CollectionInfo:
        try:
            collection = self._client.get_collection(name=name)
            count = collection.count()
            col_meta = collection.metadata or {}
            return CollectionInfo(
                name=name,
                document_count=count,
                dimension=col_meta.get("dimension", 0),
                metadata=col_meta,
            )
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to get Chroma collection info for '{name}': {e}"
            ) from e

    async def insert_documents(self, collection: str, documents: list[VectorDocument]) -> int:
        try:
            coll = self._client.get_collection(name=collection)

            ids = [doc.id for doc in documents]
            embeddings = [doc.embedding for doc in documents]
            contents = [doc.content for doc in documents]
            metadatas = [doc.metadata for doc in documents]

            coll.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas,
            )
            logger.info(
                "Inserted documents into Chroma",
                collection=collection,
                count=len(documents),
            )
            return len(documents)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to insert into Chroma collection '{collection}': {e}"
            ) from e

    async def delete_documents(self, collection: str, ids: list[str]) -> int:
        try:
            coll = self._client.get_collection(name=collection)
            coll.delete(ids=ids)
            logger.info("Deleted documents from Chroma", collection=collection, count=len(ids))
            return len(ids)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete from Chroma collection '{collection}': {e}"
            ) from e

    async def delete_by_metadata(self, collection: str, metadata_filter: dict[str, Any]) -> int:
        try:
            coll = self._client.get_collection(name=collection)

            # Build Chroma where filter
            where_filter = self._build_where_filter(metadata_filter)

            # Get matching IDs first
            results = coll.get(where=where_filter)
            matching_ids = results["ids"]

            if matching_ids:
                coll.delete(ids=matching_ids)

            logger.info(
                "Deleted by metadata from Chroma",
                collection=collection,
                count=len(matching_ids),
            )
            return len(matching_ids)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete by metadata from Chroma '{collection}': {e}"
            ) from e

    async def query(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        try:
            coll = self._client.get_collection(name=collection)

            query_params: dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            }

            if metadata_filter:
                query_params["where"] = self._build_where_filter(metadata_filter)

            results = coll.query(**query_params)

            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    content = (
                        results["documents"][0][i]
                        if results["documents"] and results["documents"][0]
                        else ""
                    )
                    metadata = (
                        results["metadatas"][0][i]
                        if results["metadatas"] and results["metadatas"][0]
                        else {}
                    )
                    # Chroma returns distances; convert to similarity score
                    distance = (
                        results["distances"][0][i]
                        if results["distances"] and results["distances"][0]
                        else 0.0
                    )
                    score = 1.0 / (1.0 + distance)

                    search_results.append(
                        VectorSearchResult(
                            id=doc_id,
                            content=content,
                            score=score,
                            metadata=metadata or {},
                        )
                    )

            return search_results
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to query Chroma collection '{collection}': {e}"
            ) from e

    async def health_check(self) -> dict[str, Any]:
        try:
            heartbeat = self._client.heartbeat()
            return {
                "status": "healthy",
                "type": "chroma",
                "heartbeat": heartbeat,
            }
        except Exception as e:
            return {"status": "unhealthy", "type": "chroma", "error": str(e)}

    async def get_document_count(self, collection: str) -> int:
        try:
            coll = self._client.get_collection(name=collection)
            return coll.count()
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to get document count for Chroma '{collection}': {e}"
            ) from e

    @staticmethod
    def _build_where_filter(metadata_filter: dict[str, Any]) -> dict[str, Any]:
        """Build a Chroma where filter from a metadata dict."""
        if len(metadata_filter) == 1:
            key, value = next(iter(metadata_filter.items()))
            return {key: {"$eq": value}}
        # Multiple conditions: use $and
        conditions = [{k: {"$eq": v}} for k, v in metadata_filter.items()]
        return {"$and": conditions}

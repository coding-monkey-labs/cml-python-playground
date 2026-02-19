"""Qdrant vector database adapter."""

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

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


class QdrantAdapter(VectorDBAdapter):
    """Adapter for Qdrant vector database."""

    def __init__(self, client: AsyncQdrantClient | None = None):
        settings = get_settings()
        if client:
            self._client = client
        else:
            self._client = AsyncQdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                grpc_port=settings.qdrant_grpc_port,
                api_key=settings.qdrant_api_key,
                prefer_grpc=settings.qdrant_prefer_grpc,
            )

    async def create_collection(
        self, name: str, dimension: int, metadata: dict[str, Any] | None = None
    ) -> None:
        try:
            await self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection", collection=name, dimension=dimension)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to create Qdrant collection '{name}': {e}"
            ) from e

    async def delete_collection(self, name: str) -> None:
        try:
            await self._client.delete_collection(collection_name=name)
            logger.info("Deleted Qdrant collection", collection=name)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete Qdrant collection '{name}': {e}"
            ) from e

    async def collection_exists(self, name: str) -> bool:
        try:
            return await self._client.collection_exists(collection_name=name)
        except Exception as e:
            raise VectorDBConnectionError(
                f"Failed to check Qdrant collection existence: {e}"
            ) from e

    async def get_collection_info(self, name: str) -> CollectionInfo:
        try:
            info = await self._client.get_collection(collection_name=name)
            return CollectionInfo(
                name=name,
                document_count=info.points_count or 0,
                dimension=info.config.params.vectors.size,  # type: ignore[union-attr]
                metadata={
                    "status": info.status.value if info.status else "unknown",
                    "optimizer_status": str(info.optimizer_status),
                },
            )
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to get Qdrant collection info for '{name}': {e}"
            ) from e

    async def insert_documents(self, collection: str, documents: list[VectorDocument]) -> int:
        try:
            points = [
                PointStruct(
                    id=doc.id,
                    vector=doc.embedding,
                    payload={"content": doc.content, **doc.metadata},
                )
                for doc in documents
            ]
            await self._client.upsert(collection_name=collection, points=points)
            logger.info(
                "Inserted documents into Qdrant",
                collection=collection,
                count=len(documents),
            )
            return len(documents)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to insert documents into Qdrant collection '{collection}': {e}"
            ) from e

    async def delete_documents(self, collection: str, ids: list[str]) -> int:
        try:
            await self._client.delete(
                collection_name=collection,
                points_selector=ids,
            )
            logger.info("Deleted documents from Qdrant", collection=collection, count=len(ids))
            return len(ids)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete documents from Qdrant collection '{collection}': {e}"
            ) from e

    async def delete_by_metadata(self, collection: str, metadata_filter: dict[str, Any]) -> int:
        try:
            qdrant_filter = self._build_filter(metadata_filter)
            # Qdrant doesn't return count on delete, so we count first
            count_result = await self._client.count(
                collection_name=collection, count_filter=qdrant_filter
            )
            pre_count = count_result.count

            await self._client.delete(
                collection_name=collection,
                points_selector=qdrant_filter,
            )
            logger.info(
                "Deleted documents by metadata from Qdrant",
                collection=collection,
                filter=metadata_filter,
                count=pre_count,
            )
            return pre_count
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete by metadata from Qdrant collection '{collection}': {e}"
            ) from e

    async def query(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        try:
            qdrant_filter = self._build_filter(metadata_filter) if metadata_filter else None
            results = await self._client.query_points(
                collection_name=collection,
                query=query_embedding,
                query_filter=qdrant_filter,
                limit=top_k,
                with_payload=True,
            )
            search_results = []
            for point in results.points:
                payload = point.payload or {}
                content = payload.pop("content", "")
                search_results.append(
                    VectorSearchResult(
                        id=str(point.id),
                        content=content,
                        score=point.score if point.score is not None else 0.0,
                        metadata=payload,
                    )
                )
            return search_results
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to query Qdrant collection '{collection}': {e}"
            ) from e

    async def health_check(self) -> dict[str, Any]:
        try:
            collections = await self._client.get_collections()
            return {
                "status": "healthy",
                "type": "qdrant",
                "collections_count": len(collections.collections),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "type": "qdrant",
                "error": str(e),
            }

    async def get_document_count(self, collection: str) -> int:
        try:
            info = await self._client.get_collection(collection_name=collection)
            return info.points_count or 0
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to get document count for Qdrant collection '{collection}': {e}"
            ) from e

    @staticmethod
    def _build_filter(metadata_filter: dict[str, Any]) -> Filter:
        """Build a Qdrant filter from a metadata dict."""
        conditions = [
            FieldCondition(key=key, match=MatchValue(value=value))
            for key, value in metadata_filter.items()
        ]
        return Filter(must=conditions)

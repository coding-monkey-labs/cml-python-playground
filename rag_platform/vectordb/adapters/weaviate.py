"""Weaviate vector database adapter."""

import uuid as uuid_mod
from typing import Any

import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import Filter, MetadataQuery

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


class WeaviateAdapter(VectorDBAdapter):
    """Adapter for Weaviate vector database."""

    def __init__(self, client: weaviate.WeaviateClient | None = None):
        settings = get_settings()
        if client:
            self._client = client
        else:
            self._client = weaviate.connect_to_local(
                host=settings.weaviate_host,
                port=settings.weaviate_port,
                grpc_port=settings.weaviate_grpc_port,
            )

    def _collection_name(self, name: str) -> str:
        """Weaviate requires PascalCase collection names. Normalize."""
        return name.replace("-", "_").replace(" ", "_").title().replace("_", "")

    async def create_collection(
        self, name: str, dimension: int, metadata: dict[str, Any] | None = None
    ) -> None:
        try:
            wv_name = self._collection_name(name)
            self._client.collections.create(
                name=wv_name,
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="doc_metadata", data_type=DataType.TEXT),
                    Property(name="original_collection", data_type=DataType.TEXT),
                ],
            )
            logger.info("Created Weaviate collection", collection=wv_name, dimension=dimension)
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("Weaviate collection already exists", collection=name)
                return
            raise VectorDBOperationError(
                f"Failed to create Weaviate collection '{name}': {e}"
            ) from e

    async def delete_collection(self, name: str) -> None:
        try:
            wv_name = self._collection_name(name)
            self._client.collections.delete(wv_name)
            logger.info("Deleted Weaviate collection", collection=wv_name)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete Weaviate collection '{name}': {e}"
            ) from e

    async def collection_exists(self, name: str) -> bool:
        try:
            wv_name = self._collection_name(name)
            return self._client.collections.exists(wv_name)
        except Exception as e:
            raise VectorDBConnectionError(
                f"Failed to check Weaviate collection existence: {e}"
            ) from e

    async def get_collection_info(self, name: str) -> CollectionInfo:
        try:
            wv_name = self._collection_name(name)
            collection = self._client.collections.get(wv_name)
            count = collection.aggregate.over_all(total_count=True).total_count or 0
            return CollectionInfo(
                name=name,
                document_count=count,
                dimension=0,  # Weaviate doesn't expose dimension directly with none vectorizer
                metadata={"weaviate_name": wv_name},
            )
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to get Weaviate collection info for '{name}': {e}"
            ) from e

    async def insert_documents(self, collection: str, documents: list[VectorDocument]) -> int:
        try:
            import json

            wv_name = self._collection_name(collection)
            coll = self._client.collections.get(wv_name)

            with coll.batch.dynamic() as batch:
                for doc in documents:
                    properties = {
                        "content": doc.content,
                        "doc_metadata": json.dumps(doc.metadata),
                        "original_collection": collection,
                    }
                    batch.add_object(
                        properties=properties,
                        vector=doc.embedding,
                        uuid=uuid_mod.uuid5(uuid_mod.NAMESPACE_DNS, doc.id),
                    )

            logger.info(
                "Inserted documents into Weaviate",
                collection=wv_name,
                count=len(documents),
            )
            return len(documents)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to insert into Weaviate collection '{collection}': {e}"
            ) from e

    async def delete_documents(self, collection: str, ids: list[str]) -> int:
        try:
            wv_name = self._collection_name(collection)
            coll = self._client.collections.get(wv_name)
            for doc_id in ids:
                wv_uuid = uuid_mod.uuid5(uuid_mod.NAMESPACE_DNS, doc_id)
                coll.data.delete_by_id(wv_uuid)
            logger.info("Deleted documents from Weaviate", collection=wv_name, count=len(ids))
            return len(ids)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete from Weaviate collection '{collection}': {e}"
            ) from e

    async def delete_by_metadata(self, collection: str, metadata_filter: dict[str, Any]) -> int:
        try:
            import json

            wv_name = self._collection_name(collection)
            coll = self._client.collections.get(wv_name)

            # Weaviate v4: delete by filter on serialized metadata
            # For Phase 2, we do a search-then-delete approach
            all_objs = coll.query.fetch_objects(limit=10000)
            to_delete = []
            for obj in all_objs.objects:
                try:
                    stored_meta = json.loads(obj.properties.get("doc_metadata", "{}"))
                    if all(stored_meta.get(k) == v for k, v in metadata_filter.items()):
                        to_delete.append(obj.uuid)
                except (json.JSONDecodeError, AttributeError):
                    continue

            for uid in to_delete:
                coll.data.delete_by_id(uid)

            logger.info(
                "Deleted by metadata from Weaviate",
                collection=wv_name,
                count=len(to_delete),
            )
            return len(to_delete)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete by metadata from Weaviate '{collection}': {e}"
            ) from e

    async def query(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        try:
            import json

            wv_name = self._collection_name(collection)
            coll = self._client.collections.get(wv_name)

            results = coll.query.near_vector(
                near_vector=query_embedding,
                limit=top_k,
                return_metadata=MetadataQuery(distance=True),
            )

            search_results = []
            for obj in results.objects:
                props = obj.properties
                content = props.get("content", "")
                try:
                    meta = json.loads(props.get("doc_metadata", "{}"))
                except (json.JSONDecodeError, TypeError):
                    meta = {}

                # Apply metadata filter client-side if provided
                if metadata_filter and not all(
                    meta.get(k) == v for k, v in metadata_filter.items()
                ):
                    continue

                score = 1.0 - (obj.metadata.distance or 0.0) if obj.metadata.distance is not None else 0.0
                search_results.append(
                    VectorSearchResult(
                        id=str(obj.uuid),
                        content=content,
                        score=score,
                        metadata=meta,
                    )
                )

            return search_results[:top_k]
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to query Weaviate collection '{collection}': {e}"
            ) from e

    async def health_check(self) -> dict[str, Any]:
        try:
            is_ready = self._client.is_ready()
            return {
                "status": "healthy" if is_ready else "unhealthy",
                "type": "weaviate",
            }
        except Exception as e:
            return {"status": "unhealthy", "type": "weaviate", "error": str(e)}

    async def get_document_count(self, collection: str) -> int:
        try:
            wv_name = self._collection_name(collection)
            coll = self._client.collections.get(wv_name)
            result = coll.aggregate.over_all(total_count=True)
            return result.total_count or 0
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to get document count for Weaviate '{collection}': {e}"
            ) from e

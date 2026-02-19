"""Service layer for query operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.core.exceptions import RAGInstanceNotFoundError
from rag_platform.core.logging import get_logger
from rag_platform.db.models.rag_instance import RAGInstance
from rag_platform.orchestrator.engine import RAGOrchestrator
from rag_platform.schemas.query import (
    CrossInstanceQueryRequest,
    QueryRequest,
    QueryResponse,
    QueryResultItem,
)
from rag_platform.vectordb.factory import get_vector_db_adapter

logger = get_logger(__name__)


class QueryService:
    """Business logic for querying RAG instances."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def _get_instance(self, instance_id: uuid.UUID) -> RAGInstance:
        """Fetch and validate a RAG instance."""
        result = await self._db.execute(
            select(RAGInstance).where(RAGInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        if not instance:
            raise RAGInstanceNotFoundError(f"RAG instance '{instance_id}' not found")
        return instance

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Execute a semantic query against a single RAG instance."""
        instance = await self._get_instance(request.rag_instance_id)

        adapter = get_vector_db_adapter(instance.vector_db_type)
        orchestrator = RAGOrchestrator(adapter)

        results = await orchestrator.query(
            collection_name=instance.namespace,
            query_text=request.query,
            embedding_model=instance.embedding_model,
            top_k=request.top_k,
            metadata_filter=request.metadata_filter,
        )

        items = [
            QueryResultItem(
                content=r.content,
                score=r.score if request.include_score else None,
                metadata=r.metadata if request.include_metadata else None,
                source_instance=instance.name,
            )
            for r in results
        ]

        return QueryResponse(
            results=items,
            total_results=len(items),
            query=request.query,
            rag_instance_id=instance.id,
        )

    async def cross_instance_query(
        self, request: CrossInstanceQueryRequest
    ) -> QueryResponse:
        """Execute a query across multiple RAG instances and merge results."""
        all_items: list[QueryResultItem] = []

        for instance_id in request.instance_ids:
            try:
                instance = await self._get_instance(instance_id)
                adapter = get_vector_db_adapter(instance.vector_db_type)
                orchestrator = RAGOrchestrator(adapter)

                results = await orchestrator.query(
                    collection_name=instance.namespace,
                    query_text=request.query,
                    embedding_model=instance.embedding_model,
                    top_k=request.top_k,
                    metadata_filter=request.metadata_filter,
                )

                for r in results:
                    all_items.append(
                        QueryResultItem(
                            content=r.content,
                            score=r.score,
                            metadata=r.metadata,
                            source_instance=instance.name,
                        )
                    )
            except Exception:
                logger.warning(
                    "Failed to query instance in cross-instance query",
                    instance_id=str(instance_id),
                )

        # Sort by score descending, take top_k
        all_items.sort(key=lambda x: x.score or 0.0, reverse=True)
        top_items = all_items[: request.top_k]

        return QueryResponse(
            results=top_items,
            total_results=len(top_items),
            query=request.query,
        )

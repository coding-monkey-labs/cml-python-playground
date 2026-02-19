"""Service layer for cross-instance federation with weighted retrieval."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_platform.core.exceptions import RAGInstanceNotFoundError, RAGPlatformError
from rag_platform.core.logging import get_logger
from rag_platform.db.models.rag_instance import RAGInstance
from rag_platform.orchestrator.engine import RAGOrchestrator
from rag_platform.schemas.query import QueryResponse, QueryResultItem
from rag_platform.schemas.versioning import FederatedQueryRequest
from rag_platform.vectordb.factory import get_vector_db_adapter

logger = get_logger(__name__)


class FederationService:
    """Business logic for federated queries across multiple RAG instances.

    Supports three merge strategies:
    - weighted_score: Multiply each result's score by the instance weight, sort globally
    - round_robin: Alternate results from each instance
    - interleave: Take top result from each instance in weight order, repeat
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def _get_instance(self, instance_id: uuid.UUID) -> RAGInstance:
        result = await self._db.execute(
            select(RAGInstance).where(RAGInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        if not instance:
            raise RAGInstanceNotFoundError(f"RAG instance '{instance_id}' not found")
        return instance

    async def federated_query(self, request: FederatedQueryRequest) -> QueryResponse:
        """Execute a federated query with weighted retrieval across instances."""
        if not request.instance_weights:
            raise RAGPlatformError("At least one instance must be specified")

        # Normalize weights
        total_weight = sum(request.instance_weights.values())
        if total_weight <= 0:
            raise RAGPlatformError("Weights must sum to a positive number")

        normalized_weights = {
            k: v / total_weight for k, v in request.instance_weights.items()
        }

        # Query each instance
        per_instance_results: dict[str, list[QueryResultItem]] = {}

        for instance_id_str, weight in normalized_weights.items():
            try:
                instance_id = uuid.UUID(instance_id_str)
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

                items = []
                for r in results:
                    weighted_score = (r.score or 0.0) * weight
                    items.append(
                        QueryResultItem(
                            content=r.content,
                            score=weighted_score,
                            metadata={
                                **(r.metadata or {}),
                                "_source_instance": instance.name,
                                "_original_score": r.score,
                                "_weight": weight,
                            },
                            source_instance=instance.name,
                        )
                    )
                per_instance_results[instance_id_str] = items

            except Exception:
                logger.warning(
                    "Failed to query instance in federation",
                    instance_id=instance_id_str,
                )
                per_instance_results[instance_id_str] = []

        # Merge results based on strategy
        if request.merge_strategy == "weighted_score":
            merged = self._merge_weighted_score(per_instance_results, request.top_k)
        elif request.merge_strategy == "round_robin":
            merged = self._merge_round_robin(per_instance_results, request.top_k)
        elif request.merge_strategy == "interleave":
            merged = self._merge_interleave(
                per_instance_results, normalized_weights, request.top_k
            )
        else:
            merged = self._merge_weighted_score(per_instance_results, request.top_k)

        return QueryResponse(
            results=merged,
            total_results=len(merged),
            query=request.query,
        )

    @staticmethod
    def _merge_weighted_score(
        per_instance: dict[str, list[QueryResultItem]], top_k: int
    ) -> list[QueryResultItem]:
        """Merge by globally sorting on weighted score."""
        all_items = []
        for items in per_instance.values():
            all_items.extend(items)
        all_items.sort(key=lambda x: x.score or 0.0, reverse=True)
        return all_items[:top_k]

    @staticmethod
    def _merge_round_robin(
        per_instance: dict[str, list[QueryResultItem]], top_k: int
    ) -> list[QueryResultItem]:
        """Merge by alternating between instances."""
        iterators = {k: iter(v) for k, v in per_instance.items() if v}
        merged: list[QueryResultItem] = []

        while len(merged) < top_k and iterators:
            exhausted = []
            for key, it in iterators.items():
                if len(merged) >= top_k:
                    break
                try:
                    merged.append(next(it))
                except StopIteration:
                    exhausted.append(key)
            for key in exhausted:
                del iterators[key]

        return merged

    @staticmethod
    def _merge_interleave(
        per_instance: dict[str, list[QueryResultItem]],
        weights: dict[str, float],
        top_k: int,
    ) -> list[QueryResultItem]:
        """Merge by interleaving in weight-priority order."""
        # Sort instances by weight descending
        sorted_instances = sorted(weights.keys(), key=lambda k: weights[k], reverse=True)

        iterators = {k: iter(per_instance.get(k, [])) for k in sorted_instances}
        merged: list[QueryResultItem] = []

        while len(merged) < top_k and iterators:
            exhausted = []
            for key in sorted_instances:
                if key not in iterators:
                    continue
                if len(merged) >= top_k:
                    break
                try:
                    merged.append(next(iterators[key]))
                except StopIteration:
                    exhausted.append(key)
            for key in exhausted:
                del iterators[key]
                sorted_instances = [k for k in sorted_instances if k in iterators]

        return merged

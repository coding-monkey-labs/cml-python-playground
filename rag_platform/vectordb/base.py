"""Abstract base class for Vector DB adapters (Adapter Pattern)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VectorDocument:
    """Represents a document to store in a vector DB."""

    id: str
    content: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorSearchResult:
    """Represents a single search result from a vector DB."""

    id: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionInfo:
    """Information about a vector DB collection/index."""

    name: str
    document_count: int
    dimension: int
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorDBAdapter(ABC):
    """Abstract adapter for vector database operations.

    Every supported vector DB must implement this interface.
    The orchestrator only interacts through this abstraction.
    """

    @abstractmethod
    async def create_collection(
        self, name: str, dimension: int, metadata: dict[str, Any] | None = None
    ) -> None:
        """Create a new collection/index in the vector DB."""

    @abstractmethod
    async def delete_collection(self, name: str) -> None:
        """Delete a collection/index from the vector DB."""

    @abstractmethod
    async def collection_exists(self, name: str) -> bool:
        """Check if a collection/index exists."""

    @abstractmethod
    async def get_collection_info(self, name: str) -> CollectionInfo:
        """Get information about a collection/index."""

    @abstractmethod
    async def insert_documents(self, collection: str, documents: list[VectorDocument]) -> int:
        """Insert documents into a collection. Returns count of inserted docs."""

    @abstractmethod
    async def delete_documents(self, collection: str, ids: list[str]) -> int:
        """Delete documents by IDs. Returns count of deleted docs."""

    @abstractmethod
    async def delete_by_metadata(self, collection: str, metadata_filter: dict[str, Any]) -> int:
        """Delete documents matching metadata filter. Returns count of deleted docs."""

    @abstractmethod
    async def query(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Query for similar documents by embedding vector."""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check health/connectivity of the vector DB. Returns status dict."""

    @abstractmethod
    async def get_document_count(self, collection: str) -> int:
        """Get total document count in a collection."""

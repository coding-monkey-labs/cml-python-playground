"""Platform-wide exception definitions."""


class RAGPlatformError(Exception):
    """Base exception for the RAG platform."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class RAGInstanceNotFoundError(RAGPlatformError):
    """Raised when a RAG instance is not found."""


class RAGInstanceAlreadyExistsError(RAGPlatformError):
    """Raised when trying to create a duplicate RAG instance."""


class VectorDBConnectionError(RAGPlatformError):
    """Raised when vector DB connection fails."""


class VectorDBOperationError(RAGPlatformError):
    """Raised when a vector DB operation fails."""


class IngestionError(RAGPlatformError):
    """Raised when document ingestion fails."""


class EmbeddingError(RAGPlatformError):
    """Raised when embedding generation fails."""


class AuthenticationError(RAGPlatformError):
    """Raised when authentication fails."""


class AuthorizationError(RAGPlatformError):
    """Raised when authorization fails."""


class PipelineError(RAGPlatformError):
    """Raised when a pipeline operation fails."""

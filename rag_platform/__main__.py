"""Entry point for running the RAG platform."""

import uvicorn

from rag_platform.core.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "rag_platform.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
    )

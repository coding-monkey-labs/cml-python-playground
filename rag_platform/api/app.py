"""FastAPI application factory."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from rag_platform.api.routes import admin, auth, ingestion, pipelines, query, rag_instances, versioning
from rag_platform.core.config import get_settings
from rag_platform.core.exceptions import RAGPlatformError
from rag_platform.core.logging import setup_logging
from rag_platform.db.base import Base
from rag_platform.db.session import engine
from rag_platform.workers.ingestion_worker import IngestionWorker

settings = get_settings()
worker = IngestionWorker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    setup_logging(settings.log_level)

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start background worker
    worker_task = asyncio.create_task(worker.start())

    yield

    # Shutdown
    await worker.stop()
    worker_task.cancel()
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="On-Prem Multi-Database RAG Orchestrator Platform",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler for platform errors
    @app.exception_handler(RAGPlatformError)
    async def platform_error_handler(request: Request, exc: RAGPlatformError):
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message, "error_type": type(exc).__name__},
        )

    # Register API routes
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(rag_instances.router, prefix="/api/v1")
    app.include_router(ingestion.router, prefix="/api/v1")
    app.include_router(query.router, prefix="/api/v1")
    app.include_router(pipelines.router, prefix="/api/v1")
    app.include_router(versioning.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")

    # Register UI routes
    from rag_platform.ui.routes import router as ui_router

    app.include_router(ui_router)

    # Mount static files
    import os

    static_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "healthy", "version": settings.app_version}

    return app


app = create_app()

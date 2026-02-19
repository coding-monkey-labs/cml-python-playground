"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from engineering_intelligence.config import get_settings
from engineering_intelligence.routers import (
    agent,
    analytics,
    auth,
    features,
    jira,
    pull_requests,
    rag,
    workflow,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup/shutdown lifecycle."""
    settings = get_settings()

    # Startup: ensure graph constraints exist
    try:
        from engineering_intelligence.graph import get_graph_client
        graph_client = get_graph_client()
        await graph_client.ensure_constraints()
    except Exception:
        pass  # Graph DB may not be available in dev

    yield

    # Shutdown: close graph connection
    try:
        from engineering_intelligence.graph import get_graph_client
        graph_client = get_graph_client()
        await graph_client.close()
    except Exception:
        pass


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Engineering Intelligence Platform — Feature Graph + Jira Graph + RAG + Temporal + Agent Integration",
        lifespan=lifespan,
    )

    # Register routers
    prefix = settings.api_prefix
    app.include_router(auth.router, prefix=prefix)
    app.include_router(features.router, prefix=prefix)
    app.include_router(jira.router, prefix=prefix)
    app.include_router(pull_requests.router, prefix=prefix)
    app.include_router(analytics.router, prefix=prefix)
    app.include_router(rag.router, prefix=prefix)
    app.include_router(workflow.router, prefix=prefix)
    app.include_router(agent.router, prefix=prefix)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "0.1.0"}

    return app


app = create_app()

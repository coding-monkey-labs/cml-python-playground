"""ObjectScale Workbench - FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.workflow import init_dependencies, router as workflow_router
from app.executors.s3_executor import S3Executor
from app.state_engine.engine import StateEngine
from app.state_engine.session_store import SessionStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize engine and session store."""
    s3_executor = S3Executor()
    engine = StateEngine(s3_executor=s3_executor)
    session_store = SessionStore()

    init_dependencies(engine, session_store)

    logger.info("ObjectScale Workbench started")
    logger.info("Available workflows: %s", [w["id"] for w in engine.list_workflows()])

    yield

    logger.info("ObjectScale Workbench shutting down")


app = FastAPI(
    title="ObjectScale Workbench",
    description="State-machine-driven UI workflow engine for S3/ObjectScale bucket management",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(workflow_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "objectscale-workbench"}

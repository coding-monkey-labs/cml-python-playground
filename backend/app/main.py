from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import jobs, pipelines, videos
from app.config import settings
from app.database import engine, Base
from app.utils.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Video Cleaner Platform...")
    # Create tables on startup (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created.")

    yield

    logger.info("Shutting down...")
    await engine.dispose()


app = FastAPI(
    title="AI Video Cleaner Platform",
    description="Modular AI-powered video processing platform",
    version="1.0.0",
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

# Mount static files for serving processed videos
import os
from pathlib import Path

media_path = Path(settings.storage_path)
media_path.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_path)), name="media")

# Include routers
app.include_router(videos.router)
app.include_router(jobs.router)
app.include_router(pipelines.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-video-cleaner"}

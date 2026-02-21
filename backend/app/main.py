import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

    # Auto-pull Ollama models in background
    if settings.ollama_auto_pull:
        asyncio.create_task(_pull_ollama_models())

    yield

    logger.info("Shutting down...")
    await engine.dispose()


async def _pull_ollama_models():
    """Pull configured Ollama models on startup (non-blocking)."""
    from app.services.intelligence.ollama_client import OllamaClient

    # Wait a few seconds for Ollama to start
    await asyncio.sleep(5)

    client = OllamaClient()
    try:
        if await client.check_health():
            results = await client.ensure_models_ready()
            for model, success in results.items():
                status = "ready" if success else "FAILED"
                logger.info(f"Ollama model '{model}': {status}")
        else:
            logger.warning(
                "Ollama not reachable at startup. Models will be pulled on first use."
            )
    except Exception as e:
        logger.warning(f"Ollama auto-pull failed: {e}")
    finally:
        await client.close()


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


@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a processed video file."""
    full_path = Path(settings.storage_path) / file_path
    if not full_path.exists():
        # Try the path as-is (absolute)
        full_path = Path(file_path)
    if not full_path.exists() or not full_path.is_file():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")

    # Ensure the path is within the storage directory (prevent path traversal)
    storage_root = Path(settings.storage_path).resolve()
    resolved = full_path.resolve()
    if not str(resolved).startswith(str(storage_root)):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=str(resolved),
        filename=resolved.name,
        media_type="video/mp4",
    )

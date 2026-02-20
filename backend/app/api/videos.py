import uuid

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.video_job import JobStatus, VideoJob
from app.schemas.video_job import VideoJobResponse
from app.utils.logging import logger
from app.utils.storage import generate_storage_path, get_upload_dir

router = APIRouter(prefix="/videos", tags=["videos"])

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"}
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB


@router.post("/upload", response_model=VideoJobResponse)
async def upload_video(
    file: UploadFile = File(...),
    pipeline_type: str = Form(default="cleaner"),
    db: AsyncSession = Depends(get_db),
):
    """Upload a video file and create a processing job."""
    # Validate file extension
    from pathlib import Path

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # Generate storage path
    upload_dir = get_upload_dir()
    storage_path = generate_storage_path(upload_dir, file.filename)

    # Stream file to disk
    try:
        async with aiofiles.open(storage_path, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):  # 1 MB chunks
                await out_file.write(chunk)
    except Exception as e:
        logger.error(f"Failed to write upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # Create job record
    job = VideoJob(
        filename=file.filename,
        input_path=str(storage_path),
        status=JobStatus.PENDING,
        pipeline_type=pipeline_type,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    logger.info(f"Created job {job.id} for file {file.filename}")

    return job


@router.get("/{job_id}", response_model=VideoJobResponse)
async def get_video_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific video job."""
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

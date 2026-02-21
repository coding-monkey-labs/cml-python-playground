import uuid
from pathlib import Path
from typing import List

import aiofiles
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.video_job import JobStatus, VideoJob
from app.schemas.video_job import VideoJobResponse
from app.utils.logging import logger
from app.utils.storage import generate_storage_path, get_upload_dir

router = APIRouter(prefix="/videos", tags=["videos"])

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"}
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB


async def _save_and_create_job(
    file: UploadFile,
    pipeline_type: str,
    db: AsyncSession,
) -> VideoJob:
    """Save a single uploaded file and create its job record."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )

    upload_dir = get_upload_dir()
    storage_path = generate_storage_path(upload_dir, file.filename)

    try:
        async with aiofiles.open(storage_path, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):
                await out_file.write(chunk)
    except Exception as e:
        logger.error(f"Failed to write upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    job = VideoJob(
        filename=file.filename,
        input_path=str(storage_path),
        status=JobStatus.PENDING,
        pipeline_type=pipeline_type,
    )
    db.add(job)
    return job


async def _trigger_n8n(job_id: uuid.UUID, pipeline_type: str) -> None:
    """Fire-and-forget webhook to n8n."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            webhook_url = f"{settings.n8n_webhook_url}/video-uploaded"
            await client.post(
                webhook_url,
                json={"job_id": str(job_id), "pipeline_type": pipeline_type},
            )
            logger.info(f"Triggered n8n pipeline for job {job_id}")
    except httpx.HTTPError as e:
        logger.warning(
            f"Failed to trigger n8n webhook for {job_id}: {e} "
            "(job will need manual trigger)"
        )


@router.post("/upload", response_model=VideoJobResponse)
async def upload_video(
    file: UploadFile = File(...),
    pipeline_type: str = Form(default="cleaner"),
    db: AsyncSession = Depends(get_db),
):
    """Upload a single video file and create a processing job."""
    job = await _save_and_create_job(file, pipeline_type, db)
    await db.commit()
    await db.refresh(job)

    logger.info(f"Created job {job.id} for file {file.filename}")
    await _trigger_n8n(job.id, pipeline_type)

    return job


@router.post("/upload-batch", response_model=list[VideoJobResponse])
async def upload_batch(
    files: List[UploadFile] = File(...),
    pipeline_type: str = Form(default="cleaner"),
    db: AsyncSession = Depends(get_db),
):
    """Upload multiple video files at once. Each gets its own processing job."""
    if len(files) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 files per batch upload",
        )

    jobs = []
    for file in files:
        try:
            job = await _save_and_create_job(file, pipeline_type, db)
            jobs.append(job)
        except HTTPException as e:
            logger.warning(f"Skipping file {file.filename}: {e.detail}")
            continue

    if not jobs:
        raise HTTPException(status_code=400, detail="No valid files in batch")

    await db.commit()

    # Refresh all jobs and trigger pipelines
    for job in jobs:
        await db.refresh(job)
        logger.info(f"Created batch job {job.id} for file {job.filename}")
        await _trigger_n8n(job.id, pipeline_type)

    return jobs


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

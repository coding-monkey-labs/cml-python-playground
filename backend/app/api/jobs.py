import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.edit_plan import EditPlan
from app.models.transcript_chunk import TranscriptChunk
from app.models.video_job import JobStatus, VideoJob
from app.schemas.edit_plan import EditPlanResponse
from app.schemas.transcript_chunk import TranscriptChunkResponse
from app.schemas.video_job import (
    VideoJobListResponse,
    VideoJobResponse,
    VideoJobStatusUpdate,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=VideoJobListResponse)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all video processing jobs with pagination."""
    query = select(VideoJob).order_by(VideoJob.created_at.desc())

    if status:
        query = query.where(VideoJob.status == status)

    # Get total count
    count_query = select(func.count()).select_from(VideoJob)
    if status:
        count_query = count_query.where(VideoJob.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    result = await db.execute(query.offset(skip).limit(limit))
    jobs = result.scalars().all()

    return VideoJobListResponse(jobs=jobs, total=total)


@router.patch("/{job_id}/status", response_model=VideoJobResponse)
async def update_job_status(
    job_id: uuid.UUID,
    update: VideoJobStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update the status of a job (used by pipeline services)."""
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = update.status
    if update.error_message:
        job.error_message = update.error_message

    await db.commit()
    await db.refresh(job)
    return job


@router.get("/{job_id}/transcript", response_model=list[TranscriptChunkResponse])
async def get_job_transcript(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get transcript chunks for a job."""
    result = await db.execute(
        select(TranscriptChunk)
        .where(TranscriptChunk.job_id == job_id)
        .order_by(TranscriptChunk.start_time)
    )
    chunks = result.scalars().all()
    return chunks


@router.get("/{job_id}/edit-plan", response_model=list[EditPlanResponse])
async def get_job_edit_plan(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get edit plan for a job."""
    result = await db.execute(
        select(EditPlan)
        .where(EditPlan.job_id == job_id)
        .order_by(EditPlan.start_time)
    )
    plans = result.scalars().all()
    return plans

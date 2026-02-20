import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.video_job import JobStatus, VideoJob
from app.services.ingestion.audio_extractor import extract_audio
from app.services.ingestion.transcriber import transcribe_audio
from app.services.intelligence.edit_plan_generator import generate_edit_plan
from app.services.editing.renderer import apply_edit_plan
from app.utils.logging import logger

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.post("/{job_id}/ingest")
async def run_ingestion(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Run ingestion pipeline: extract audio and transcribe."""
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        # Step 1: Extract audio
        job.status = JobStatus.EXTRACTING_AUDIO
        await db.commit()
        logger.info(f"[{job_id}] Extracting audio...")

        audio_path = await extract_audio(job.input_path, job_id)
        job.audio_path = audio_path

        # Step 2: Transcribe
        job.status = JobStatus.TRANSCRIBING
        await db.commit()
        logger.info(f"[{job_id}] Transcribing audio...")

        chunks = await transcribe_audio(audio_path, job_id, db)

        job.status = JobStatus.ANALYZING
        await db.commit()

        return {
            "status": "success",
            "job_id": str(job_id),
            "audio_path": audio_path,
            "chunk_count": len(chunks),
        }

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        await db.commit()
        logger.error(f"[{job_id}] Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/analyze")
async def run_analysis(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Run intelligence analysis and generate edit plan."""
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.status = JobStatus.GENERATING_EDIT_PLAN
        await db.commit()
        logger.info(f"[{job_id}] Generating edit plan...")

        edit_plan = await generate_edit_plan(job_id, db)

        return {
            "status": "success",
            "job_id": str(job_id),
            "edit_count": len(edit_plan),
        }

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        await db.commit()
        logger.error(f"[{job_id}] Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/edit")
async def run_editing(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Apply edit plan and render output video."""
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.status = JobStatus.EDITING
        await db.commit()
        logger.info(f"[{job_id}] Applying edits...")

        output_path = await apply_edit_plan(job_id, db)

        job.status = JobStatus.COMPLETED
        job.output_path = output_path
        await db.commit()

        return {
            "status": "success",
            "job_id": str(job_id),
            "output_path": output_path,
        }

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        await db.commit()
        logger.error(f"[{job_id}] Editing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

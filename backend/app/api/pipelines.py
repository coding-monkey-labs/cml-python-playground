import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.edit_plan import EditPlan
from app.models.transcript_chunk import TranscriptChunk
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
        job.error_message = None
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
        job.error_message = None
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
    """Apply approved edit plan items and render output video."""
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.status = JobStatus.EDITING
        job.error_message = None
        await db.commit()
        logger.info(f"[{job_id}] Applying approved edits...")

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


@router.post("/{job_id}/retry")
async def retry_pipeline(
    job_id: uuid.UUID,
    from_step: str = "auto",
    db: AsyncSession = Depends(get_db),
):
    """Retry a failed or stuck job from a specific step.

    from_step options:
    - "auto": detect where to resume based on current state
    - "ingest": restart from audio extraction
    - "analyze": restart from analysis
    - "edit": restart from editing
    """
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Determine which step to retry from
    if from_step == "auto":
        if job.status in (JobStatus.PENDING, JobStatus.FAILED):
            # Check what data we have to figure out where to resume
            if not job.audio_path:
                from_step = "ingest"
            else:
                chunk_result = await db.execute(
                    select(TranscriptChunk)
                    .where(TranscriptChunk.job_id == job_id)
                    .limit(1)
                )
                has_chunks = chunk_result.scalar_one_or_none() is not None

                plan_result = await db.execute(
                    select(EditPlan)
                    .where(EditPlan.job_id == job_id)
                    .limit(1)
                )
                has_plan = plan_result.scalar_one_or_none() is not None

                if not has_chunks:
                    from_step = "ingest"
                elif not has_plan:
                    from_step = "analyze"
                else:
                    from_step = "edit"
        else:
            # Map current status to appropriate retry step
            status_to_step = {
                JobStatus.EXTRACTING_AUDIO: "ingest",
                JobStatus.TRANSCRIBING: "ingest",
                JobStatus.ANALYZING: "analyze",
                JobStatus.GENERATING_EDIT_PLAN: "analyze",
                JobStatus.EDITING: "edit",
                JobStatus.RENDERING: "edit",
            }
            from_step = status_to_step.get(job.status, "ingest")

    # Clear error and reset
    job.error_message = None
    job.status = JobStatus.PENDING
    await db.commit()

    logger.info(f"[{job_id}] Retrying pipeline from step: {from_step}")

    # Clean up stale data for the step we're retrying
    if from_step == "ingest":
        await db.execute(
            delete(TranscriptChunk).where(TranscriptChunk.job_id == job_id)
        )
        await db.execute(
            delete(EditPlan).where(EditPlan.job_id == job_id)
        )
        await db.commit()
    elif from_step == "analyze":
        await db.execute(
            delete(EditPlan).where(EditPlan.job_id == job_id)
        )
        await db.commit()

    return {
        "status": "retrying",
        "job_id": str(job_id),
        "from_step": from_step,
    }

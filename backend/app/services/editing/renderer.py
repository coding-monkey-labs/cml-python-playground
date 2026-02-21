"""Video rendering engine: applies edit plan and produces cleaned output."""

import shutil
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.edit_plan import EditPlan
from app.models.video_job import VideoJob
from app.services.editing.ffmpeg_wrapper import (
    cut_segments,
    get_video_info,
    normalize_audio,
    reduce_noise,
)
from app.utils.logging import logger
from app.utils.storage import get_processed_dir


async def apply_edit_plan(job_id: uuid.UUID, db: AsyncSession) -> str:
    """Apply edit plan to a video and render the cleaned output.

    Only applies edits that have been approved (approved=True).

    Steps:
    1. Load approved edit plan entries
    2. Calculate keep segments (inverse of removes)
    3. Cut and concatenate
    4. Apply noise reduction
    5. Normalize audio
    6. Return output path
    """
    # Load job
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    # Load APPROVED edit plan entries only
    result = await db.execute(
        select(EditPlan)
        .where(EditPlan.job_id == job_id)
        .where(EditPlan.approved.is_(True))
        .where(EditPlan.action.in_(["remove", "compress"]))
        .order_by(EditPlan.start_time)
    )
    edits = result.scalars().all()

    output_dir = get_processed_dir()
    ext = Path(job.input_path).suffix

    if not edits:
        logger.info(f"[{job_id}] No approved edits to apply")
        if settings.noise_reduction_enabled:
            # Still apply noise reduction even with no cuts
            nr_path = str(output_dir / f"{job_id}_nr{ext}")
            output_path = str(output_dir / f"{job_id}_cleaned{ext}")
            await reduce_noise(job.input_path, nr_path)
            await normalize_audio(nr_path, output_path)
            Path(nr_path).unlink(missing_ok=True)
        else:
            output_path = str(output_dir / f"{job_id}_cleaned{ext}")
            shutil.copy2(job.input_path, output_path)
        return output_path

    # Get video info
    video_info = await get_video_info(job.input_path)
    total_duration = video_info.duration

    # Calculate keep segments (inverse of remove segments)
    remove_regions = [(e.start_time, e.end_time) for e in edits if e.action == "remove"]
    keep_segments = _calculate_keep_segments(remove_regions, total_duration)

    if not keep_segments:
        raise ValueError("Edit plan would remove entire video")

    logger.info(
        f"[{job_id}] Removing {len(remove_regions)} approved segments, "
        f"keeping {len(keep_segments)} segments"
    )

    # Step 1: Cut and concatenate
    cut_path = str(output_dir / f"{job_id}_cut{ext}")
    await cut_segments(job.input_path, cut_path, keep_segments)

    # Step 2: Noise reduction
    if settings.noise_reduction_enabled:
        nr_path = str(output_dir / f"{job_id}_nr{ext}")
        await reduce_noise(cut_path, nr_path)
        Path(cut_path).unlink(missing_ok=True)
        cut_path = nr_path

    # Step 3: Normalize audio
    output_path = str(output_dir / f"{job_id}_cleaned{ext}")
    await normalize_audio(cut_path, output_path)

    # Cleanup intermediate file
    Path(cut_path).unlink(missing_ok=True)

    # Calculate time saved
    removed_duration = sum(end - start for start, end in remove_regions)
    logger.info(
        f"[{job_id}] Rendered output: {output_path} "
        f"(removed {removed_duration:.1f}s of {total_duration:.1f}s)"
    )

    return output_path


def _calculate_keep_segments(
    remove_regions: list[tuple[float, float]],
    total_duration: float,
    min_segment_duration: float = 0.1,
) -> list[tuple[float, float]]:
    """Calculate segments to keep by inverting remove regions."""
    if not remove_regions:
        return [(0.0, total_duration)]

    # Sort and merge overlapping remove regions
    sorted_removes = sorted(remove_regions, key=lambda x: x[0])
    merged = [sorted_removes[0]]
    for start, end in sorted_removes[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Generate keep segments
    keep = []
    current = 0.0

    for rm_start, rm_end in merged:
        if rm_start > current + min_segment_duration:
            keep.append((current, rm_start))
        current = rm_end

    if current < total_duration - min_segment_duration:
        keep.append((current, total_duration))

    return keep

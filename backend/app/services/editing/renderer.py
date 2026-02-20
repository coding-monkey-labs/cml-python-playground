"""Video rendering engine: applies edit plan and produces cleaned output."""

import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.edit_plan import EditPlan
from app.models.video_job import VideoJob
from app.services.editing.ffmpeg_wrapper import (
    cut_segments,
    get_video_info,
    normalize_audio,
)
from app.utils.logging import logger
from app.utils.storage import get_processed_dir


async def apply_edit_plan(job_id: uuid.UUID, db: AsyncSession) -> str:
    """Apply edit plan to a video and render the cleaned output.

    Steps:
    1. Load edit plan (segments to remove)
    2. Calculate keep segments (inverse)
    3. Cut and concatenate
    4. Normalize audio
    5. Return output path
    """
    # Load job
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    # Load edit plan
    result = await db.execute(
        select(EditPlan)
        .where(EditPlan.job_id == job_id)
        .where(EditPlan.action.in_(["remove", "compress"]))
        .order_by(EditPlan.start_time)
    )
    edits = result.scalars().all()

    if not edits:
        logger.info(f"[{job_id}] No edits to apply, copying original")
        output_dir = get_processed_dir()
        output_path = output_dir / f"{job_id}_cleaned{Path(job.input_path).suffix}"
        import shutil
        shutil.copy2(job.input_path, str(output_path))
        return str(output_path)

    # Get video info
    video_info = await get_video_info(job.input_path)
    total_duration = video_info.duration

    # Calculate keep segments (inverse of remove segments)
    remove_regions = [(e.start_time, e.end_time) for e in edits if e.action == "remove"]
    keep_segments = _calculate_keep_segments(remove_regions, total_duration)

    if not keep_segments:
        raise ValueError("Edit plan would remove entire video")

    logger.info(
        f"[{job_id}] Removing {len(remove_regions)} segments, "
        f"keeping {len(keep_segments)} segments"
    )

    # Cut and concatenate
    output_dir = get_processed_dir()
    cut_path = str(output_dir / f"{job_id}_cut{Path(job.input_path).suffix}")
    output_path = str(output_dir / f"{job_id}_cleaned{Path(job.input_path).suffix}")

    await cut_segments(job.input_path, cut_path, keep_segments)

    # Normalize audio in the final output
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

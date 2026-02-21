"""Edit plan generator that combines local scoring with Ollama LLM analysis."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.edit_plan import EditPlan
from app.models.transcript_chunk import TranscriptChunk
from app.services.intelligence.ollama_client import OllamaClient
from app.services.intelligence.segment_scorer import (
    SegmentScores,
    score_segment,
    should_remove_segment,
)
from app.utils.logging import logger


async def generate_edit_plan(
    job_id: uuid.UUID,
    db: AsyncSession,
) -> list[EditPlan]:
    """Generate a complete edit plan for a video job.

    Steps:
    1. Score all transcript chunks
    2. Apply local rule-based detection
    3. Detect silence gaps
    4. Ollama LLM strategic review
    5. Merge all sources into final edit plan
    """
    # Load transcript chunks
    result = await db.execute(
        select(TranscriptChunk)
        .where(TranscriptChunk.job_id == job_id)
        .order_by(TranscriptChunk.start_time)
    )
    chunks = result.scalars().all()

    if not chunks:
        logger.warning(f"[{job_id}] No transcript chunks found")
        return []

    # Step 1: Score all segments
    logger.info(f"[{job_id}] Scoring {len(chunks)} segments...")
    scored_segments = []
    for chunk in chunks:
        duration = chunk.end_time - chunk.start_time
        scores = score_segment(
            text=chunk.text,
            duration=duration,
            word_count=chunk.word_count,
            confidence=chunk.confidence,
        )

        # Update chunk with scores
        chunk.clarity_score = scores.clarity_score
        chunk.engagement_score = scores.engagement_score
        chunk.filler_score = scores.filler_score
        chunk.retention_risk_score = scores.retention_risk_score

        scored_segments.append((chunk, scores))

    await db.commit()

    # Step 2: Generate local edit plan
    local_edits = []
    for chunk, scores in scored_segments:
        if should_remove_segment(scores):
            reason = _determine_removal_reason(scores)
            local_edits.append(
                {
                    "start": chunk.start_time,
                    "end": chunk.end_time,
                    "action": "remove",
                    "reason": reason,
                    "confidence": _calculate_confidence(scores),
                    "source": "local",
                }
            )
        elif scores.filler_score > 0.3:
            local_edits.append(
                {
                    "start": chunk.start_time,
                    "end": chunk.end_time,
                    "action": "flag",
                    "reason": f"Moderate filler content (score: {scores.filler_score:.2f})",
                    "confidence": scores.filler_score,
                    "source": "local",
                }
            )

    # Step 3: Detect silence/pause compression opportunities
    silence_edits = _detect_silence_gaps(chunks)
    local_edits.extend(silence_edits)

    logger.info(f"[{job_id}] Local analysis: {len(local_edits)} edits")

    # Step 4: Ollama LLM strategic review
    all_edits = list(local_edits)
    try:
        transcript_text = " ".join(c.text for c in chunks)
        ollama = OllamaClient(model=settings.ollama_reviewer_model)
        try:
            ollama_edits = await ollama.review_edit_plan(
                transcript_text, local_edits
            )
            for edit in ollama_edits:
                if edit.get("source") == "ollama":
                    all_edits.append(edit)
            new_count = len(ollama_edits) - len(local_edits)
            if new_count > 0:
                logger.info(f"[{job_id}] Ollama added {new_count} suggestions")
        finally:
            await ollama.close()
    except Exception as e:
        logger.warning(f"[{job_id}] Ollama review skipped: {e}")

    # Step 5: Deduplicate and merge overlapping edits
    merged_edits = _merge_overlapping_edits(all_edits)
    logger.info(f"[{job_id}] Final edit plan: {len(merged_edits)} edits")

    # Store edit plans in DB
    db_plans = []
    for edit in merged_edits:
        plan = EditPlan(
            job_id=job_id,
            start_time=edit["start"],
            end_time=edit["end"],
            action=edit.get("action", "remove"),
            reason=edit.get("reason", ""),
            confidence=edit.get("confidence", 0.0),
            source=edit.get("source", "merged"),
        )
        db.add(plan)
        db_plans.append(plan)

    await db.commit()
    return db_plans


def _determine_removal_reason(scores: SegmentScores) -> str:
    reasons = []
    if scores.filler_score >= 0.6:
        reasons.append("filler repetition")
    if scores.clarity_score <= 0.3:
        reasons.append("low clarity")
    if scores.engagement_score <= 0.2:
        reasons.append("low engagement")
    if scores.retention_risk_score >= 0.7:
        reasons.append("high retention risk")
    return "; ".join(reasons) if reasons else "poor quality segment"


def _calculate_confidence(scores: SegmentScores) -> float:
    return (
        scores.filler_score * 0.3
        + (1.0 - scores.clarity_score) * 0.3
        + scores.retention_risk_score * 0.4
    )


def _detect_silence_gaps(chunks: list[TranscriptChunk]) -> list[dict]:
    """Detect gaps between transcript chunks that indicate long pauses."""
    edits = []
    threshold = settings.silence_threshold_seconds

    for i in range(1, len(chunks)):
        gap = chunks[i].start_time - chunks[i - 1].end_time
        if gap > threshold:
            edits.append(
                {
                    "start": chunks[i - 1].end_time,
                    "end": chunks[i].start_time,
                    "action": "compress",
                    "reason": f"Long pause ({gap:.1f}s)",
                    "confidence": min(gap / 5.0, 1.0),
                    "source": "local",
                }
            )

    return edits


def _merge_overlapping_edits(edits: list[dict]) -> list[dict]:
    """Merge overlapping or adjacent edit regions."""
    if not edits:
        return []

    sorted_edits = sorted(edits, key=lambda e: e["start"])
    merged = [sorted_edits[0]]

    for edit in sorted_edits[1:]:
        prev = merged[-1]
        if edit["start"] <= prev["end"] + 0.5:
            prev["end"] = max(prev["end"], edit["end"])
            prev["confidence"] = max(prev["confidence"], edit.get("confidence", 0.0))
            if edit.get("reason") and edit["reason"] not in prev.get("reason", ""):
                prev["reason"] = f"{prev.get('reason', '')}; {edit['reason']}"
            prev["source"] = "merged"
        else:
            merged.append(edit)

    return merged

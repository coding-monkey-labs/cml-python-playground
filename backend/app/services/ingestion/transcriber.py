import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.transcript_chunk import TranscriptChunk
from app.services.intelligence.filler_detector import is_filler_phrase
from app.utils.logging import logger


async def transcribe_audio(
    audio_path: str, job_id: uuid.UUID, db: AsyncSession
) -> list[TranscriptChunk]:
    """Transcribe audio using faster-whisper and store chunks in the database.

    Returns list of created TranscriptChunk records.
    """
    from faster_whisper import WhisperModel

    logger.info(
        f"[{job_id}] Loading Whisper model ({settings.whisper_model_size})..."
    )
    model = WhisperModel(
        settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )

    logger.info(f"[{job_id}] Transcribing {audio_path}...")
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=200,
        ),
    )

    logger.info(
        f"[{job_id}] Detected language: {info.language} "
        f"(probability: {info.language_probability:.2f})"
    )

    chunks = []
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue

        word_count = len(text.split())
        filler = is_filler_phrase(text)

        chunk = TranscriptChunk(
            job_id=job_id,
            start_time=segment.start,
            end_time=segment.end,
            text=text,
            confidence=segment.avg_logprob if segment.avg_logprob else 0.0,
            word_count=word_count,
            is_filler=filler,
        )
        db.add(chunk)
        chunks.append(chunk)

    await db.commit()
    logger.info(f"[{job_id}] Stored {len(chunks)} transcript chunks")
    return chunks

import asyncio
import uuid
from pathlib import Path

from app.config import settings
from app.utils.logging import logger
from app.utils.storage import get_audio_dir


async def extract_audio(input_video_path: str, job_id: uuid.UUID) -> str:
    """Extract and normalize audio from video using FFmpeg.

    Returns the path to the extracted WAV file.
    """
    audio_dir = get_audio_dir()
    output_path = audio_dir / f"{job_id}.wav"

    cmd = [
        "ffmpeg",
        "-i",
        input_video_path,
        "-vn",                      # No video
        "-acodec",
        "pcm_s16le",                # PCM 16-bit
        "-ar",
        "16000",                    # 16kHz sample rate (optimal for Whisper)
        "-ac",
        "1",                        # Mono
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11",  # Normalize audio levels
        "-threads",
        str(settings.ffmpeg_threads),
        "-y",                       # Overwrite output
        str(output_path),
    ]

    logger.info(f"[{job_id}] Running FFmpeg audio extraction...")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
        logger.error(f"[{job_id}] FFmpeg failed: {error_msg}")
        raise RuntimeError(f"Audio extraction failed: {error_msg}")

    if not output_path.exists():
        raise RuntimeError(f"Audio file not created at {output_path}")

    logger.info(f"[{job_id}] Audio extracted to {output_path}")
    return str(output_path)


async def get_video_duration(video_path: str) -> float:
    """Get duration of a video file in seconds using FFprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError("Failed to get video duration")

    return float(stdout.decode().strip())

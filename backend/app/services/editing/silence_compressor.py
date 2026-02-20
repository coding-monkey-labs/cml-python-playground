"""Silence compression: reduces long pauses in video."""

import asyncio

from app.config import settings
from app.utils.logging import logger


async def compress_silence(
    input_path: str,
    output_path: str,
    silence_threshold_db: float = -30.0,
    min_silence_duration: float = 0.5,
    target_silence_duration: float = 0.3,
) -> str:
    """Compress silences in a video using FFmpeg's silenceremove filter.

    This reduces long pauses while keeping short natural pauses intact.
    """
    # Use a combination of silencedetect and atempo to compress silent parts
    # The approach: detect silence, then use aselect to speed through silent parts
    audio_filter = (
        f"silenceremove="
        f"start_periods=0:"
        f"start_duration={min_silence_duration}:"
        f"start_threshold={silence_threshold_db}dB:"
        f"detection=peak,"
        f"aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-af", audio_filter,
        "-c:v", "copy",
        "-threads", str(settings.ffmpeg_threads),
        output_path,
    ]

    logger.info(f"Compressing silence in {input_path}...")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode()
        logger.error(f"Silence compression failed: {error_msg}")
        raise RuntimeError(f"Silence compression failed: {error_msg}")

    logger.info(f"Silence compressed: {output_path}")
    return output_path


async def detect_silence_regions(
    audio_path: str,
    noise_threshold_db: float = -30.0,
    min_duration: float = 0.5,
) -> list[dict]:
    """Detect silence regions in an audio file.

    Returns list of {start, end, duration} for each silence region.
    """
    cmd = [
        "ffmpeg",
        "-i", audio_path,
        "-af", f"silencedetect=noise={noise_threshold_db}dB:d={min_duration}",
        "-f", "null",
        "-",
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    output = stderr.decode()
    regions = []
    current_start = None

    for line in output.split("\n"):
        if "silence_start:" in line:
            try:
                current_start = float(line.split("silence_start:")[1].strip().split()[0])
            except (IndexError, ValueError):
                continue
        elif "silence_end:" in line and current_start is not None:
            try:
                parts = line.split("silence_end:")[1].strip().split()
                end = float(parts[0])
                duration = float(parts[-1]) if len(parts) > 1 else end - current_start
                regions.append(
                    {
                        "start": current_start,
                        "end": end,
                        "duration": duration,
                    }
                )
                current_start = None
            except (IndexError, ValueError):
                continue

    return regions

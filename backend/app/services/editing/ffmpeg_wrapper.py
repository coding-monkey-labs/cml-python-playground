"""FFmpeg wrapper for video editing operations."""

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from app.config import settings
from app.utils.logging import logger


@dataclass
class VideoInfo:
    duration: float
    width: int
    height: int
    fps: float
    codec: str
    audio_codec: str
    bitrate: int


async def get_video_info(video_path: str) -> VideoInfo:
    """Probe video file for metadata using FFprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_path,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"FFprobe failed: {stderr.decode()}")

    data = json.loads(stdout.decode())

    video_stream = next(
        (s for s in data.get("streams", []) if s["codec_type"] == "video"), {}
    )
    audio_stream = next(
        (s for s in data.get("streams", []) if s["codec_type"] == "audio"), {}
    )
    fmt = data.get("format", {})

    # Parse frame rate
    fps_str = video_stream.get("r_frame_rate", "30/1")
    num, den = fps_str.split("/")
    fps = float(num) / float(den) if float(den) > 0 else 30.0

    return VideoInfo(
        duration=float(fmt.get("duration", 0)),
        width=int(video_stream.get("width", 0)),
        height=int(video_stream.get("height", 0)),
        fps=fps,
        codec=video_stream.get("codec_name", "unknown"),
        audio_codec=audio_stream.get("codec_name", "unknown"),
        bitrate=int(fmt.get("bit_rate", 0)),
    )


async def cut_segments(
    input_path: str,
    output_path: str,
    keep_segments: list[tuple[float, float]],
) -> str:
    """Cut video keeping only the specified time segments.

    Uses FFmpeg's concat demuxer for frame-accurate cuts.
    """
    if not keep_segments:
        raise ValueError("No segments to keep")

    # Create temporary segment files
    temp_dir = Path(output_path).parent / "temp_segments"
    temp_dir.mkdir(parents=True, exist_ok=True)
    concat_file = temp_dir / "concat.txt"
    segment_files = []

    try:
        # Extract each keep segment
        for i, (start, end) in enumerate(keep_segments):
            segment_path = temp_dir / f"segment_{i:04d}.ts"
            segment_files.append(segment_path)

            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(start),
                "-i", input_path,
                "-t", str(end - start),
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                "-threads", str(settings.ffmpeg_threads),
                str(segment_path),
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Segment extraction failed: {stderr.decode()}")
                raise RuntimeError(f"Failed to extract segment {i}")

        # Write concat file
        with open(concat_file, "w") as f:
            for seg_path in segment_files:
                f.write(f"file '{seg_path}'\n")

        # Concatenate all segments
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            "-threads", str(settings.ffmpeg_threads),
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Concatenation failed: {stderr.decode()}")

        logger.info(f"Output rendered to {output_path}")
        return output_path

    finally:
        # Cleanup temp files
        for f in segment_files:
            f.unlink(missing_ok=True)
        concat_file.unlink(missing_ok=True)
        if temp_dir.exists():
            try:
                temp_dir.rmdir()
            except OSError:
                pass


async def normalize_audio(input_path: str, output_path: str) -> str:
    """Normalize audio levels in a video file."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v", "copy",
        "-threads", str(settings.ffmpeg_threads),
        output_path,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"Audio normalization failed: {stderr.decode()}")

    return output_path


async def reduce_noise(input_path: str, output_path: str) -> str:
    """Remove background noise from audio using FFmpeg's afftdn filter.

    afftdn = Adaptive FFT-based Denoiser
    - nr: noise reduction amount in dB (higher = more aggressive)
    - nf: noise floor in dB
    - tn: enable noise tracking (adapts to changing noise)
    """
    nr_db = int(settings.noise_reduction_strength * 50)  # Map 0-1 to 0-50 dB
    audio_filter = (
        f"afftdn=nr={nr_db}:nf=-25:tn=1,"
        f"highpass=f=80,"        # Remove rumble below 80Hz
        f"lowpass=f=13000"       # Remove hiss above 13kHz
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

    logger.info(f"Applying noise reduction (strength={settings.noise_reduction_strength})...")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode()
        logger.error(f"Noise reduction failed: {error_msg}")
        raise RuntimeError(f"Noise reduction failed: {error_msg}")

    logger.info(f"Noise reduction applied: {output_path}")
    return output_path

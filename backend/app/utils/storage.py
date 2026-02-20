import os
import shutil
import uuid
from pathlib import Path

from app.config import settings


def get_upload_dir() -> Path:
    path = Path(settings.storage_path) / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_audio_dir() -> Path:
    path = Path(settings.storage_path) / "audio"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_processed_dir() -> Path:
    path = Path(settings.storage_path) / "processed"
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_storage_path(directory: Path, original_filename: str) -> Path:
    """Generate a unique storage path preserving the file extension."""
    ext = Path(original_filename).suffix
    unique_name = f"{uuid.uuid4()}{ext}"
    return directory / unique_name


def cleanup_job_files(job_id: str) -> None:
    """Remove all files associated with a job."""
    for directory in [get_upload_dir(), get_audio_dir(), get_processed_dir()]:
        for f in directory.iterdir():
            if job_id in f.name:
                f.unlink(missing_ok=True)

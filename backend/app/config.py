from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://videocleaner:changeme_in_production@localhost:5432/videocleaner"

    # Storage
    storage_path: str = "/data/videos"

    # Ollama (all models are open-source, Ollama-hosted)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"
    ollama_reviewer_model: str = "llama3:8b"
    ollama_auto_pull: bool = True

    # Whisper
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    # n8n
    n8n_webhook_url: str = "http://n8n:5678/webhook"

    # FFmpeg
    ffmpeg_threads: int = 4

    # Audio noise removal
    noise_reduction_enabled: bool = True
    noise_reduction_strength: float = 0.21  # afftdn noise floor (0.0-1.0)

    # Scoring thresholds
    filler_score_threshold: float = 0.4
    engagement_score_threshold: float = 0.3
    silence_threshold_seconds: float = 1.5

    # Batch processing
    max_concurrent_jobs: int = 3

    model_config = {"env_file": ".env"}


settings = Settings()

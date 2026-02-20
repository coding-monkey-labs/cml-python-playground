from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://videocleaner:changeme_in_production@localhost:5432/videocleaner"

    # Storage
    storage_path: str = "/data/videos"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"

    # Claude
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Whisper
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    # n8n
    n8n_webhook_url: str = "http://n8n:5678/webhook"

    # FFmpeg
    ffmpeg_threads: int = 4

    # Scoring thresholds
    filler_score_threshold: float = 0.4
    engagement_score_threshold: float = 0.3
    silence_threshold_seconds: float = 1.5

    model_config = {"env_file": ".env"}


settings = Settings()

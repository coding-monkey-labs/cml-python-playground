"""Tests for configuration settings."""

from engineering_intelligence.config.settings import Settings


class TestSettings:
    def test_defaults(self):
        settings = Settings()
        assert settings.app_name == "Engineering Intelligence Platform"
        assert settings.debug is False
        assert settings.api_prefix == "/api/v1"
        assert settings.access_token_expire_minutes == 60
        assert settings.embedding_dimensions == 1536

    def test_database_url_default(self):
        settings = Settings()
        assert "postgresql+asyncpg" in settings.database_url

    def test_temporal_defaults(self):
        settings = Settings()
        assert settings.temporal_host == "localhost:7233"
        assert settings.temporal_namespace == "default"
        assert settings.temporal_task_queue == "eng-intel-queue"

# tests/test_config.py
import pytest
from app.config import settings


def test_settings_exist():
    """Test that settings are properly loaded"""
    assert settings.DATABASE_URL is not None
    assert settings.SPARK_MASTER is not None
    assert settings.API_PORT > 0


def test_default_values():
    """Test default configuration values"""
    assert settings.ENV in ["development", "production", "test"]
    assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]
    assert settings.API_HOST == "0.0.0.0"

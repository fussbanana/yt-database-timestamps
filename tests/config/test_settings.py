"""
Gezielte Tests für settings.py (Fehlerfälle, Edge Cases)
"""

import os
import pytest
from pydantic import ValidationError
from yt_database.config.settings import Settings


def test_settings_defaults():
    s = Settings()
    assert isinstance(s.debug, bool)
    assert isinstance(s.database_url, str)
    assert isinstance(s.api_key, str)


def test_settings_env(monkeypatch):
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("API_KEY", "testkey")
    s = Settings()
    assert s.debug is True
    assert s.database_url == "sqlite:///test.db"
    assert s.api_key == "testkey"


def test_settings_invalid_type(monkeypatch):
    monkeypatch.setenv("DEBUG", "notabool")
    with pytest.raises(ValidationError):
        Settings()

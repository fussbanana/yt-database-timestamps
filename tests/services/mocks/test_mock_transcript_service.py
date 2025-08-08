"""
Unit-Tests für MockTranscriptService.

Testet die Rückgabe von Beispiel-Transkript und Metadaten.
"""

import pytest

from yt_database.services.mocks.mock_transcript_service import MockTranscriptService


@pytest.mark.unit
class TestMockTranscriptService:
    def test_fetch_transcript_returns_mock_data(self):
        service = MockTranscriptService()
        result = service.fetch_transcript("abc123")
        assert "transcript" in result
        assert "metadata" in result
        assert result["metadata"]["video_id"] == "abc123"
        assert isinstance(result["transcript"], list)
        assert result["transcript"][0]["text"] == "Mock-Text"

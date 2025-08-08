# tests/services/test_channel_video_worker.py
"""
Unit Tests für ChannelVideoWorker.

Testet die asynchrone Transcript-Lade-Funktionalität.
"""

import pytest
from unittest.mock import Mock, patch

from yt_database.services.channel_video_worker import ChannelVideoWorker
from yt_database.models.models import TranscriptData


class TestChannelVideoWorker:
    """Test-Klasse für ChannelVideoWorker."""

    def test_channel_video_worker_import(self):
        """Test: ChannelVideoWorker kann importiert werden."""
        assert ChannelVideoWorker is not None

    @pytest.fixture
    def mock_service_factory(self):
        """Mock ServiceFactory für Tests."""
        factory = Mock()
        factory.get_transcript_service.return_value = Mock()
        factory.get_project_manager_service.return_value = Mock()
        return factory

    def test_worker_initialization(self, mock_service_factory):
        """Test: Worker kann korrekt initialisiert werden."""
        worker = ChannelVideoWorker(
            service_factory=mock_service_factory, channel_url="https://www.youtube.com/@test", force_download=False
        )

        assert worker.service_factory == mock_service_factory
        assert worker.channel_url == "https://www.youtube.com/@test"
        assert worker.force_download is False

    @patch("yt_database.database.Channel")
    def test_force_download_calls_transcript_service(self, mock_channel, mock_service_factory):
        """Test: Force-Download verwendet TranscriptService."""
        # Mock transcript service
        mock_transcript_service = Mock()
        mock_transcript_service.fetch_channel_metadata.return_value = [
            TranscriptData(
                video_id="test123",
                title="Test Transcript",
                channel_id="UC123",
                channel_name="Test Channel",
                channel_url="https://www.youtube.com/@test",
                video_url="https://www.youtube.com/watch?v=test123",
                publish_date="2025-01-01",
                duration="10:00",
                entries=[],
                error_reason="",
            )
        ]
        mock_service_factory.get_transcript_service.return_value = mock_transcript_service

        worker = ChannelVideoWorker(
            service_factory=mock_service_factory, channel_url="https://www.youtube.com/@test", force_download=True
        )

        # Mock signal emission
        videos_emitted = []
        finished_called = [False]

        def capture_videos(videos):
            videos_emitted.extend(videos)

        def capture_finished():
            finished_called[0] = True

        worker.videos_loaded.connect(capture_videos)
        worker.finished.connect(capture_finished)

        # Run worker
        worker.run()

        # Verify transcript service was called
        mock_transcript_service.fetch_channel_metadata.assert_called_once_with("https://www.youtube.com/@test")

        # Verify signals were emitted
        assert finished_called[0] is True
        assert len(videos_emitted) == 1
        assert videos_emitted[0].video_id == "test123"

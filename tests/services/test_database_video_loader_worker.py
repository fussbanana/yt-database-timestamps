# tests/services/test_database_video_loader_worker.py
"""
Unit Tests für DatabaseVideoLoaderWorker.

Testet die asynchrone Datenbank-Transcript-Lade-Funktionalität.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from yt_database.services.database_video_loader_worker import DatabaseVideoLoaderWorker
from yt_database.database import Transcript


class TestDatabaseVideoLoaderWorker:
    """Test-Klasse für DatabaseVideoLoaderWorker."""

    def test_database_video_loader_worker_import(self):
        """Test: DatabaseVideoLoaderWorker kann importiert werden."""
        assert DatabaseVideoLoaderWorker is not None

    @pytest.fixture
    def mock_project_manager_service(self):
        """Mock ProjectManagerService für Tests."""
        service = Mock()
        service.get_transcript_path_for_video_id.return_value = "/path/to/transcript.md"
        return service

    @pytest.fixture
    def mock_video(self):
        """Mock Transcript-Objekt für Tests."""
        video = Mock(spec=Transcript)
        video.video_id = "test123"
        video.title = "Test Transcript"
        video.channel_name = "Test Channel"
        video.video_url = "https://www.youtube.com/watch?v=test123"
        video.is_transcribed = True
        video.has_chapters = False
        return video

    def test_worker_initialization(self, mock_project_manager_service):
        """Test: Worker kann korrekt initialisiert werden."""
        worker = DatabaseVideoLoaderWorker(project_manager_service=mock_project_manager_service)

        assert worker.pm_service == mock_project_manager_service

    @patch("os.path.exists")
    @patch("os.listdir")
    @patch("os.path.isdir")
    def test_run_loads_videos_successfully(
        self, mock_isdir, mock_listdir, mock_exists, mock_project_manager_service, mock_video
    ):
        """Test: Worker lädt Videos erfolgreich aus der Datenbank."""
        # Setup mocks für Transcript-Objekt
        mock_video.video_id = "test123"
        mock_video.channel_id = "UC123"

        # Setup mocks für Dateisystem
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = ["test123"]  # Transcript-Verzeichnis existiert

        # Setup ProjectManager mock
        mock_project_manager_service.projects_dir = "./projects"

        worker = DatabaseVideoLoaderWorker(
            project_manager_service=mock_project_manager_service,
            videos=[mock_video],  # Videos direkt übergeben statt DB-Abfrage
        )

        # Mock signal emission
        videos_emitted = []
        finished_called = [False]
        progress_updates = []

        def capture_videos(video_batch):
            videos_emitted.extend(video_batch)

        def capture_finished():
            finished_called[0] = True

        def capture_progress(current, total):
            progress_updates.append((current, total))

        worker.videos_loaded.connect(capture_videos)
        worker.finished.connect(capture_finished)
        worker.progress.connect(capture_progress)

        # Run worker
        worker.run()

        # Verify that no DB calls were made (da Videos direkt übergeben wurden)
        # (Removed Transcript.select() assertion since we don't mock it anymore)

        # Verify signals were emitted
        assert finished_called[0] is True
        assert len(videos_emitted) == 1
        assert len(progress_updates) == 1
        assert progress_updates[0] == (1, 1)

        # Verify enriched video structure
        enriched_video = videos_emitted[0]
        assert enriched_video["video"] == mock_video
        assert enriched_video["has_transcript"] is True
        assert "has_chapters" in enriched_video
        assert "transcript_path" in enriched_video

    @patch("yt_database.services.database_video_loader_worker.Transcript")
    def test_run_handles_empty_database(self, mock_video_model, mock_project_manager_service):
        """Test: Worker behandelt leere Datenbank korrekt."""
        # Setup mocks
        mock_video_model.select.return_value = []

        worker = DatabaseVideoLoaderWorker(project_manager_service=mock_project_manager_service)

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

        # Verify signals were emitted correctly
        assert finished_called[0] is True
        assert len(videos_emitted) == 0

    @patch("yt_database.services.database_video_loader_worker.Transcript")
    def test_run_handles_database_error(self, mock_video_model, mock_project_manager_service):
        """Test: Worker behandelt Datenbankfehler korrekt."""
        # Setup mocks
        mock_video_model.select.side_effect = Exception("Database error")

        worker = DatabaseVideoLoaderWorker(project_manager_service=mock_project_manager_service)

        # Mock signal emission
        error_emitted = []

        def capture_error(error_msg):
            error_emitted.append(error_msg)

        worker.error.connect(capture_error)

        # Run worker
        worker.run()

        # Verify error signal was emitted
        assert len(error_emitted) == 1
        assert "Database error" in error_emitted[0]

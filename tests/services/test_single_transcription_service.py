# -*- coding: utf-8 -*-
"""
Unittests für den SingleTranscriptionService.
"""

import pytest
from unittest.mock import MagicMock
from yt_database.models.models import TranscriptData, TranscriptEntry
from yt_database.services.single_transcription_service import SingleTranscriptionService
from yt_database.services.protocols import (
    FileServiceProtocol,
    FormatterServiceProtocol,
    ProjectManagerProtocol,
    TranscriptServiceProtocol,
)


@pytest.fixture
def mock_transcript_service():
    """Fixture für einen gemockten TranscriptService."""
    return MagicMock(spec=TranscriptServiceProtocol)


@pytest.fixture
def mock_formatter_service():
    """Fixture für einen gemockten FormatterService."""
    return MagicMock(spec=FormatterServiceProtocol)


@pytest.fixture
def mock_file_service():
    """Fixture für einen gemockten FileService."""
    return MagicMock(spec=FileServiceProtocol)


@pytest.fixture
def mock_project_manager():
    """Fixture für einen gemockten ProjectManager."""
    return MagicMock(spec=ProjectManagerProtocol)


@pytest.fixture
def single_transcription_service(
    mock_transcript_service,
    mock_formatter_service,
    mock_file_service,
    mock_project_manager,
):
    """Fixture, die eine Instanz des SingleTranscriptionService mit gemockten Abhängigkeiten zurückgibt."""
    return SingleTranscriptionService(
        transcript_service=mock_transcript_service,
        formatter_service=mock_formatter_service,
        file_service=mock_file_service,
        project_manager=mock_project_manager,
    )


def test_process_video_success(single_transcription_service, mock_transcript_service, mock_file_service):
    """Testet den erfolgreichen Durchlauf der process_video-Methode."""
    initial_data = TranscriptData(video_id="vid123", channel_id="chan123", channel_name="Test")
    fetched_data = TranscriptData(
        video_id="vid123",
        channel_id="chan123",
        channel_name="Test",
        entries=[TranscriptEntry(text="hello", start=0.0, end=1.0)],
    )

    mock_transcript_service.fetch_transcript.return_value = fetched_data

    result = single_transcription_service.process_video(initial_data)

    mock_transcript_service.fetch_transcript.assert_called_once_with("vid123")
    mock_file_service.write_transcript_file.assert_called_once_with(fetched_data)
    assert result == fetched_data
    assert not result.error_reason


def test_process_video_fetch_error(single_transcription_service, mock_transcript_service, mock_file_service):
    """Testet den Fall, dass das Abrufen des Transkripts fehlschlägt."""
    initial_data = TranscriptData(video_id="vid123", channel_id="chan123", channel_name="Test")
    fetched_data = TranscriptData(video_id="vid123", channel_id="chan123", channel_name="Test", error_reason="Fetch failed")

    mock_transcript_service.fetch_transcript.return_value = fetched_data

    result = single_transcription_service.process_video(initial_data)

    mock_transcript_service.fetch_transcript.assert_called_once_with("vid123")
    mock_file_service.write_transcript_file.assert_not_called()
    assert result.error_reason == "Fetch failed"


def test_process_video_empty_transcript(single_transcription_service, mock_transcript_service, mock_file_service):
    """Testet den Fall, dass das abgerufene Transkript leer ist."""
    initial_data = TranscriptData(video_id="vid123", channel_id="chan123", channel_name="Test")
    fetched_data = TranscriptData(video_id="vid123", channel_id="chan123", channel_name="Test", entries=[])

    mock_transcript_service.fetch_transcript.return_value = fetched_data

    result = single_transcription_service.process_video(initial_data)

    mock_transcript_service.fetch_transcript.assert_called_once_with("vid123")
    mock_file_service.write_transcript_file.assert_not_called()
    assert result.error_reason == "Transkript ist leer oder nicht vorhanden."

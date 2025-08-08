# -*- coding: utf-8 -*-
"""
Unittests für den FileService.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from yt_database.config.settings import Settings
from yt_database.models.models import TranscriptData
from yt_database.services.file_service import FileService


@pytest.fixture
def mock_settings(tmp_path):
    """Fixture, die eine Mock-Settings-Instanz mit einem temporären Projektpfad zurückgibt."""
    settings = MagicMock(spec=Settings)
    settings.project_path = str(tmp_path)
    return settings


@pytest.fixture
def file_service(mock_settings):
    """Fixture, die eine Instanz des FileService mit Mock-Settings zurückgibt."""
    return FileService(settings=mock_settings)


@pytest.fixture
def sample_transcript_data():
    """Fixture, die ein Beispiel-TranscriptData-Objekt zurückgibt."""
    return TranscriptData(
        title="A Test Video",
        video_id="vid123",
        channel_id="chan123",
        channel_handle="@testchannel",
        channel_name="Test Channel",
        video_url="http://example.com/vid123",
        entries=[],
        chapters=[],
    )


def test_write_and_read(file_service, tmp_path):
    """Testet das Schreiben und Lesen einer einfachen Textdatei."""
    file_path = tmp_path / "test.txt"
    content = "Hello, world!"
    file_service.write(str(file_path), content)
    assert os.path.exists(file_path)
    read_content = file_service.read(str(file_path))
    assert read_content == content


def test_read_file_not_found(file_service):
    """Testet, ob eine FileNotFoundError ausgelöst wird, wenn eine Datei nicht existiert."""
    with pytest.raises(FileNotFoundError):
        file_service.read("non_existent_file.txt")


@patch("yt_database.services.file_service.to_snake_case")
def test_write_transcript_file(mock_to_snake_case, file_service, sample_transcript_data, tmp_path):
    """Testet das Schreiben einer vollständigen Transkriptdatei."""
    mock_to_snake_case.return_value = "a_test_video"

    with patch.object(file_service, "_update_transcript_database_status") as mock_update_db:
        file_service.write_transcript_file(sample_transcript_data)

        expected_dir = tmp_path / "@testchannel" / "vid123"
        expected_file = expected_dir / "a_test_video_transcript.md"

        assert os.path.exists(expected_file)

        with open(expected_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "title: A Test Video" in content
            assert "video_id: vid123" in content
            assert "channel_handle: @testchannel" in content
            assert "## Transkript" in content

        mock_update_db.assert_called_once_with(sample_transcript_data)


@patch("yt_database.database.Channel")
@patch("yt_database.database.Transcript")
def test_update_transcript_database_status(mock_transcript, mock_channel, file_service, sample_transcript_data):
    """Testet die Aktualisierung des Datenbankstatus für ein Transkript."""
    mock_channel.get_or_create.return_value = (MagicMock(), True)
    mock_transcript.get_or_create.return_value = (MagicMock(), True)

    file_service._update_transcript_database_status(sample_transcript_data)

    mock_channel.get_or_create.assert_called_once()
    mock_transcript.get_or_create.assert_called_once()

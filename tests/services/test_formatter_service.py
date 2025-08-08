# -*- coding: utf-8 -*-
"""
Unittests für den FormatterService.
"""

import json
import os
import pytest
from unittest.mock import MagicMock
from yt_database.models.models import TranscriptData, ChapterEntry, TranscriptEntry
from yt_database.services.formatter_service import FormatterService


@pytest.fixture
def formatter_service():
    """Fixture, die eine Instanz des FormatterService zurückgibt."""
    return FormatterService()


@pytest.fixture
def sample_transcript_data():
    """Fixture, die ein Beispiel-TranscriptData-Objekt zurückgibt."""
    return TranscriptData(
        title="Test Video",
        video_id="vid123",
        channel_id="chan123",
        video_url="http://example.com/vid123",
        channel_name="Test Channel",
        channel_url="http://example.com/channel/test",
        channel_handle="@test",
        publish_date="2025-01-01",
        duration="00:01:00",
        chapters=[
            ChapterEntry(title="Intro", start=0.0, end=10.0, start_hms="00:00:00", end_hms="00:00:10"),
        ],
        entries=[
            TranscriptEntry(text="Hello world", start=1.0, end=2.0, start_hms="00:00:01", speaker=""),
        ],
    )


def test_format_seconds_to_hms(formatter_service):
    """Testet die Umwandlung von Sekunden in das HMS-Format."""
    assert formatter_service.format_seconds_to_hms(3661) == "01:01:01"
    assert formatter_service.format_seconds_to_hms(59) == "00:00:59"
    assert formatter_service.format_seconds_to_hms(0) == "00:00:00"


def test_extract_metadata(formatter_service):
    """Testet die Extraktion und Vereinheitlichung von Metadaten."""
    raw_metadata = {
        "id": "vid123",
        "uploader_id": "chan123",
        "uploader": "Test Channel",
        "original_url": "http://youtube.com/watch?v=vid123",
        "title": "A Great Video",
        "upload_date": "20250101",
        "duration_string": "1:00",
    }
    extracted = formatter_service.extract_metadata(raw_metadata)
    assert extracted["video_id"] == "vid123"
    assert extracted["channel_id"] == "chan123"
    assert extracted["channel_name"] == "Test Channel"
    assert extracted["title"] == "A Great Video"
    assert extracted["publish_date"] == "20250101"
    assert extracted["duration"] == "1:00"
    assert extracted["youtube_url"] == "http://youtube.com/watch?v=vid123"


def test_format_transcript_data(formatter_service, sample_transcript_data):
    """Testet die Formatierung eines TranscriptData-Objekts in einen String."""
    output = formatter_service.format(sample_transcript_data)
    assert "Metadaten" in output
    assert "title: Test Video" in output
    assert "video_id: vid123" in output
    assert "Kapitel mit Zeitstempeln" in output
    assert "- Intro (00:00:00 - 00:00:10)" in output
    assert "Transkript" in output
    assert "[00:00:01] Hello world" in output


def test_parse_json3_transcript(formatter_service, tmp_path):
    """Testet das Parsen einer .json3-Transkriptdatei."""
    json3_content = {
        "events": [
            {
                "tStartMs": 1000,
                "dDurationMs": 2000,
                "segs": [{"utf8": "Hello "}, {"utf8": "world"}],
            },
            {
                "tStartMs": 3000,
                "dDurationMs": 1000,
                "segs": [{"utf8": "ähm this is a test"}],
            },
        ]
    }
    file_path = tmp_path / "transcript.json3"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json3_content, f)

    result = formatter_service.parse_json3_transcript(str(file_path))
    assert len(result) == 2
    assert result[0]["text"] == "Hello world"
    assert result[0]["start"] == 1.0
    assert result[0]["duration"] == 2.0
    assert result[1]["text"] == "this is a test"  # "ähm" should be filtered
    assert result[1]["start"] == 3.0


def test_parse_json3_transcript_file_not_found(formatter_service):
    """Testet das Verhalten, wenn die .json3-Datei nicht gefunden wird."""
    result = formatter_service.parse_json3_transcript("non_existent_file.json3")
    assert result == []

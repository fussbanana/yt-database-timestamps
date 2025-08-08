"""
Unittests für das Pydantic-Modul models.py.
"""

import pytest
from src.yt_database.models.models import (
    TranscriptEntry,
    ChapterEntry,
    TranscriptData,
)


def test_transcript_entry_creation():
    """Testet die Erstellung eines TranscriptEntry-Objekts."""
    entry = TranscriptEntry(
        text="Hello world",
        start=0.5,
        end=1.5,
        duration=1.0,
        start_hms="00:00:00,500",
        end_hms="00:00:01,500",
        duration_hms="00:00:01,000",
        speaker="Speaker 1",
    )
    assert entry.text == "Hello world"
    assert entry.start == 0.5
    assert entry.speaker == "Speaker 1"


def test_chapter_entry_creation():
    """Testet die Erstellung eines ChapterEntry-Objekts."""
    chapter = ChapterEntry(
        title="Introduction",
        start=0.0,
        end=10.5,
        start_hms="00:00:00,000",
        end_hms="00:00:10,500",
    )
    assert chapter.title == "Introduction"
    assert chapter.end == 10.5


def test_transcript_data_creation():
    """Testet die Erstellung eines TranscriptData-Objekts."""
    entry = TranscriptEntry(text="Test entry", start=0.0, end=1.0)
    chapter = ChapterEntry(title="Test chapter", start=0.0, end=1.0)

    transcript_data = TranscriptData(
        title="Test Video",
        video_id="vid123",
        channel_id="chan123",
        channel_name="Test Channel",
        video_url="http://example.com/vid123",
        entries=[entry],
        chapters=[chapter],
        detailed_chapters=[chapter],
    )
    assert transcript_data.title == "Test Video"
    assert transcript_data.video_id == "vid123"
    assert len(transcript_data.entries) == 1
    assert transcript_data.entries[0].text == "Test entry"
    assert len(transcript_data.chapters) == 1
    assert transcript_data.chapters[0].title == "Test chapter"


def test_transcript_data_defaults():
    """Testet die Standardwerte eines TranscriptData-Objekts."""
    transcript_data = TranscriptData(
        video_id="vid_defaults",
        channel_id="chan_defaults",
        channel_name="Default Channel",
    )
    assert transcript_data.title == ""
    assert transcript_data.video_url == ""
    assert transcript_data.publish_date == ""
    assert transcript_data.duration == ""
    assert transcript_data.entries == []
    assert transcript_data.chapters == []
    assert transcript_data.detailed_chapters == []
    assert transcript_data.error_reason == ""

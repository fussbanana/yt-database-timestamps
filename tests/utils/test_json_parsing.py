"""
Unittests für das Modul json_parsing.py

Testet die wichtigsten Funktionen für das Parsen und Serialisieren von JSON.
"""

import pytest
from yt_database.utils import json_parsing


def test_parse_channel_videos_json(tmp_path):
    import json
    from yt_database.models.models import TranscriptData
    # Dummy-Daten
    data = [
        {
            "id": "abc123",
            "url": "https://yt.com/abc123",
            "channel_id": "chan1",
            "channel_url": "https://yt.com/channel/chan1",
            "title": "Testvideo",
            "publish_date": "2025-01-01",
            "duration": "10:00",
            "error_reason": ""
        }
    ]
    file_path = tmp_path / "test.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    # Funktion aufrufen
    result = json_parsing.parse_channel_videos_json(str(file_path))
    assert isinstance(result, list)
    assert isinstance(result[0], TranscriptData)
    assert result[0].video_id == "abc123"
    assert result[0].title == "Testvideo"
    assert result[0].channel_name == tmp_path.name

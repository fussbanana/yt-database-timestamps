"""
Hilfsfunktionen zum Parsen von Transcript-Listen aus JSON-Dateien.

Funktionen:
    parse_channel_videos_json(path: str) -> List[Transcript]

Alle öffentlichen Funktionen sind mit Google-Style-Docstrings versehen und strikt typisiert.
"""

import json
import os
from typing import List

from yt_database.models.models import TranscriptData


def parse_channel_videos_json(path: str) -> List[TranscriptData]:
    """
    Parst eine JSON-Datei mit Transcript-Informationen und gibt eine Liste von TranscriptData-Objekten zurück.

    Args:
        path (str): Pfad zur JSON-Datei.

    Returns:
        List[TranscriptData]: Liste von validierten Transkriptionsdaten.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    channel_name = os.path.basename(os.path.dirname(path))
    transcript_list = []
    for entry in data:
        transcript = TranscriptData(
            video_id=entry.get("id", ""),
            video_url=entry.get("url", ""),
            channel_id=entry.get("channel_id", ""),
            channel_name=channel_name,
            channel_url=entry.get("channel_url", ""),
            title=entry.get("title", ""),
            publish_date=entry.get("publish_date", ""),
            duration=entry.get("duration", ""),
            entries=[],
            chapters=[],
            error_reason=entry.get("error_reason", ""),
        )
        transcript_list.append(transcript)
    return transcript_list


if __name__ == "__main__":
    path = "/home/sascha/PycharmProjects/yt-database/channel_metadata_raw.json"
    videos = parse_channel_videos_json(path)
    for video in videos:
        print(f"Transcript ID: {video.video_id}, Title: {video.title}, Channel: {video.channel_name}")

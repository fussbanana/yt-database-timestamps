"""
Hilfsfunktion zum Ermitteln des Transkript-Dateipfads für ein Transcript.
Google-Style Docstring, PEP8, Typisierung.
"""

import os
from typing import Optional


def get_transcript_path_for_video_id(projects_dir: str, channel_id: str, video_id: str) -> Optional[str]:
    """
    Sucht die Transkriptdatei für ein Transcript anhand der IDs und gibt den Pfad zurück.

    Args:
        projects_dir (str): Basisverzeichnis für Projekte.
        channel_id (str): Kanal-ID.
        video_id (str): Transcript-ID.

    Returns:
        Optional[str]: Absoluter Pfad zur Transkriptdatei oder None, falls nicht gefunden.
    """
    video_dir = os.path.join(projects_dir, channel_id, video_id)
    if not os.path.isdir(video_dir):
        return None
    for fname in os.listdir(video_dir):
        if fname.endswith("_transcript.md"):
            return os.path.join(video_dir, fname)
    return None

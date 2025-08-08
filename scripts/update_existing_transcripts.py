#!/usr/bin/env python3
"""
Script zum Aktualisieren existierender Transkripte in der Datenbank.

Durchsucht alle Transkript-Dateien und aktualisiert die Datenbankeinträge
mit den korrekten transcript_lines Werten.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger
from yt_database.database import Transcript, Channel
from yt_database.services.file_service import FileService


def count_transcript_lines(file_path: Path) -> int:
    """Zählt die Anzahl der Transkriptzeilen in einer .md Datei."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Zähle Zeilen mit Zeitstempel-Pattern [HH:MM:SS-HH:MM:SS]
        lines = content.split("\n")
        transcript_lines = 0

        for line in lines:
            line = line.strip()
            if line.startswith("[") and "]" in line and "-" in line:
                # Pattern: [00:00:05-00:00:10] content
                if line.count(":") >= 4:  # mindestens 2 Zeitstempel
                    transcript_lines += 1

        return transcript_lines
    except Exception as e:
        logger.error(f"Fehler beim Zählen der Transkriptzeilen in {file_path}: {e}")
        return 0


def update_existing_transcripts():
    """Aktualisiert alle existierenden Transkripte in der Datenbank."""
    logger.info("Starte Aktualisierung existierender Transkripte...")

    projects_dir = Path("projects")
    if not projects_dir.exists():
        logger.error("Projects-Verzeichnis nicht gefunden")
        return

    updated_count = 0

    # Durchsuche alle Transkript-Dateien
    for transcript_file in projects_dir.rglob("*_transcript.md"):
        try:
            # Extrahiere video_id aus dem Pfad
            # Pfad: projects/@CHANNEL/VIDEO_ID/filename_transcript.md
            video_id = transcript_file.parent.name

            if not video_id or video_id.startswith("@"):
                continue

            # Suche Transcript in der Datenbank
            try:
                transcript = Transcript.get(Transcript.video_id == video_id)
            except Exception:
                logger.warning(f"Transcript für video_id {video_id} nicht in Datenbank gefunden")
                continue

            # Zähle Transkriptzeilen
            transcript_lines = count_transcript_lines(transcript_file)

            # Aktualisiere Datenbank
            transcript.transcript_lines = transcript_lines
            transcript.is_transcribed = transcript_lines > 0
            transcript.save()

            logger.info(f"Aktualisiert: {video_id} -> {transcript_lines} Zeilen")
            updated_count += 1

        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten von {transcript_file}: {e}")
            continue

    logger.info(f"Aktualisierung abgeschlossen. {updated_count} Transkripte aktualisiert.")


if __name__ == "__main__":
    update_existing_transcripts()

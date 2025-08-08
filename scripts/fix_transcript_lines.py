#!/usr/bin/env python3
"""
Repariert transcript_lines für bestehende Videos in der Datenbank
"""

import os
from pathlib import Path
from yt_database.database import initialize_database, Transcript
from yt_database.utils.utils import to_snake_case
from yt_database.gui.utils.icons import Icons


def fix_transcript_lines():
    """Repariert transcript_lines für Videos mit vorhandenen Transcript-Dateien"""
    initialize_database()

    print("Suche Videos mit is_transcribed=True aber transcript_lines=0...")

    # Hole alle Videos mit is_transcribed=True aber transcript_lines=0
    broken_videos = list(Transcript.select().where(Transcript.is_transcribed == True, Transcript.transcript_lines == 0))

    print(f"Gefunden: {len(broken_videos)} Videos zum Reparieren")

    fixed_count = 0
    for video in broken_videos:
        # Erstelle den erwarteten Pfad zur Transcript-Datei
        # Basierend auf der Struktur: projects/@CHANNEL_HANDLE/VIDEO_ID/*_transcript.md
        channel_handle = video.channel.handle or f"@{video.channel.name.replace(' ', '')}"
        # Verwende den projects-Ordner relativ zum Skript
        projects_dir = Path(__file__).parent.parent / "projects"
        video_dir = projects_dir / channel_handle / video.video_id

        # Finde alle Transcript-Dateien in dem Video-Verzeichnis
        transcript_files = list(video_dir.glob("*_transcript.md"))

        if transcript_files:
            transcript_path = transcript_files[0]  # Nimm die erste gefundene Datei
            try:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    transcript_lines = sum(1 for line in f if line.strip())

                # Update das Video
                Transcript.update(transcript_lines=transcript_lines).where(
                    Transcript.video_id == video.video_id
                ).execute()

                print(f"{Icons.get(Icons.CHECK).name} {video.video_id}: {transcript_lines} Zeilen gesetzt ({transcript_path.name})")
                fixed_count += 1

            except Exception as e:
                print(f"{Icons.get(Icons.X).name} {video.video_id}: Fehler beim Lesen der Datei: {e}")
        else:
            print(f"? {video.video_id}: Keine Transcript-Datei gefunden in {video_dir}")

    print(f"\nReparatur abgeschlossen: {fixed_count} Videos repariert")


if __name__ == "__main__":
    fix_transcript_lines()

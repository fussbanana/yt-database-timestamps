"""
FileService

Service-Klasse zum Schreiben und Lesen von Textdateien und YAML-Metadaten für YouTube-Projekte.
Erstellt Verzeichnisse automatisch, loggt alle Dateioperationen und bietet Methoden für Transkript- und Metadatenmanagement.
"""

import os
from typing import Any

from loguru import logger

from yt_database.config.settings import Settings, settings
from yt_database.models.models import TranscriptData
from yt_database.services.protocols import FileServiceProtocol
from yt_database.utils.utils import to_snake_case


class FileService(FileServiceProtocol):
    """
    Service-Klasse zum Schreiben und Lesen von Dateien und Metadaten.

    Args:
        settings (Settings): Globale Settings für Pfade und Konfiguration.

    Example:
        >>> service = FileService()
        >>> service.write("output.txt", "Hallo Welt")
    """

    def __init__(self, settings: Settings = settings) -> None:
        """
        Initialisiert den FileService mit Settings.

        Args:
            settings (Settings): Globale Settings für Pfade und Konfiguration.
        """
        logger.debug("Initialisiere FileService mit Settings.")
        self.settings = settings

    def write_transcript_file(self, transcript: TranscriptData) -> None:
        """
        Schreibt die vollständige TranscriptData als Markdown in die Datei mit folgender Struktur:
        --- Metadaten ---
        ## Kapitel mit Zeitstempeln
        ## Detaillierte Kapitel
        ## Transkript

        Args:
            transcript (TranscriptData): Transkript-Datenstruktur.

        Example:
            >>> service = FileService()
            >>> transcript = TranscriptData(video_id="BaW_jenozKc", channel_id="@99ZUEINS", title="Mein Transcript", ...)
            >>> service.write_transcript_file(transcript)
        """
        title = transcript.title
        safe_title = to_snake_case(title)
        projects_dir = self.settings.project_path
        transcript_path = f"{projects_dir}/{transcript.channel_handle}/{transcript.video_id}/{safe_title}_transcript.md"

        # Metadaten-Block
        meta_lines = ["---\n"]
        meta_lines.append(f"title: {transcript.title}\n")
        meta_lines.append(f"video_id: {transcript.video_id}\n")
        meta_lines.append(f"video_url: {transcript.video_url}\n")
        meta_lines.append(f"channel_name: {transcript.channel_name}\n")
        meta_lines.append(f"channel_url: {transcript.channel_url}\n")
        meta_lines.append(f"channel_handle: {transcript.channel_handle}\n")
        meta_lines.append(f"publish_date: {transcript.publish_date}\n")
        meta_lines.append(f"duration: {transcript.duration}\n")
        meta_lines.append(f"transcript_lines: {len(transcript.entries) if transcript.entries else 0}\n")
        meta_lines.append(f"chapters: {len(transcript.chapters) if transcript.chapters else 0}\n")
        meta_lines.append(
            f"detailed_chapters: {len(transcript.detailed_chapters) if transcript.detailed_chapters else 0}\n"
        )
        meta_lines.append(f"error: {transcript.error_reason}\n")
        meta_lines.append("---\n\n")

        # Kapitel-Block (für YouTube-Kommentare)
        chapter_lines = ["", "## Kapitel mit Zeitstempeln"]
        if transcript.chapters:
            for chapter in transcript.chapters:
                chapter_lines.append(f"- {chapter.start_hms}-{chapter.end_hms} {chapter.title}\n")
        else:
            chapter_lines.append("\n\n\n")

        # Detaillierte Kapitel-Block (für Datenbank)
        detailed_chapter_lines = ["", "## Detaillierte Kapitel"]
        if transcript.detailed_chapters:
            detailed_chapter_lines.append("```")
            for chapter in transcript.detailed_chapters:
                detailed_chapter_lines.append(f"• {chapter.start_hms}: {chapter.title}\n")
            detailed_chapter_lines.append("```")
        else:
            detailed_chapter_lines.append("\n\n\n")

        # Transkript-Block
        transcript_lines = ["", "## Transkript\n\n", ""]
        for entry in transcript.entries:
            speaker = f"[{entry.speaker}] " if entry.speaker else ""
            transcript_lines.append(f"[{entry.start_hms}-{entry.end_hms}] {speaker}{entry.text}\n")

        # Zusammenführen und schreiben
        all_lines = meta_lines + chapter_lines + detailed_chapter_lines + transcript_lines
        full_text = "".join(all_lines)
        self.write(transcript_path, full_text)
        logger.debug(f"Transkript geschrieben: {transcript_path}")

        # Datenbankeintrag aktualisieren
        self._update_transcript_database_status(transcript)

    def _update_transcript_database_status(self, transcript: TranscriptData) -> None:
        """
        Aktualisiert den Datenbankeintrag für das Transkript mit dem Status.

        Args:
            transcript (TranscriptData): Transkript-Datenstruktur.
        """
        try:
            from yt_database.database import Channel, Transcript

            # Prüfe ob Transkript-Daten vorhanden sind
            has_transcript = transcript.entries and len(transcript.entries) > 0
            has_chapters = transcript.chapters and len(transcript.chapters) > 0
            chapter_count = len(transcript.chapters) if transcript.chapters else 0
            detailed_chapter_count = len(transcript.detailed_chapters) if transcript.detailed_chapters else 0
            transcript_lines_count = len(transcript.entries) if transcript.entries else 0

            # Hole oder erstelle Channel (mit besserem Error Handling für handle)
            try:
                channel, created = Channel.get_or_create(
                    channel_id=transcript.channel_id,
                    defaults={
                        "name": transcript.channel_name,
                        "url": transcript.channel_url,
                        "handle": transcript.channel_handle,
                    },
                )
            except Exception as channel_error:
                # Fallback: Versuche ohne handle falls UNIQUE constraint Problem
                if "UNIQUE constraint failed: channel.handle" in str(channel_error):
                    logger.warning(f"Handle-Konflikt für Channel {transcript.channel_id}, versuche ohne handle")
                    channel, created = Channel.get_or_create(
                        channel_id=transcript.channel_id,
                        defaults={
                            "name": transcript.channel_name,
                            "url": transcript.channel_url,
                            "handle": None,  # Setze handle auf None bei Konflikt
                        },
                    )
                else:
                    raise channel_error

            # Aktualisiere oder erstelle Transcript-Eintrag
            transcript_entry, created = Transcript.get_or_create(
                video_id=transcript.video_id,
                defaults={
                    "title": transcript.title,
                    "video_url": transcript.video_url,
                    "publish_date": transcript.publish_date,
                    "duration": transcript.duration,
                    "channel": channel,
                    "is_transcribed": has_transcript,
                    "has_chapters": has_chapters,
                    "chapter_count": chapter_count,
                    "detailed_chapter_count": detailed_chapter_count,
                    "transcript_lines": transcript_lines_count,
                    "error_reason": transcript.error_reason or "",
                },
            )

            # Wenn nicht neu erstellt, aktualisiere die Felder
            if not created:
                transcript_entry.is_transcribed = has_transcript
                transcript_entry.has_chapters = has_chapters
                transcript_entry.chapter_count = chapter_count
                transcript_entry.detailed_chapter_count = detailed_chapter_count
                transcript_entry.transcript_lines = transcript_lines_count
                transcript_entry.error_reason = transcript.error_reason or ""
                transcript_entry.save()

            logger.debug(
                f"Datenbankeintrag {'erstellt' if created else 'aktualisiert'} für Video {transcript.video_id}: transkribiert={has_transcript}, Kapitel={has_chapters} (einfach: {chapter_count}, detailliert: {detailed_chapter_count}), transcript_lines={transcript_lines_count}"
            )

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Datenbankeintrags für Video {transcript.video_id}: {e}")

    def write(self, path: str, content: Any) -> None:
        """
        Schreibt den gegebenen Inhalt in die angegebene Datei.

        Erstellt das Zielverzeichnis falls nötig und überschreibt bestehende Dateien.

        Args:
            path (str): Zielpfad der Datei.
            content (Any): Beliebiger Inhalt, der als String gespeichert wird.

        Example:
            >>> service = FileService()
            >>> service.write("output.txt", "Hallo Welt")
        """
        # Ich ermittle das Verzeichnis aus dem Pfad.
        dir_path = os.path.dirname(path)
        if dir_path:
            # Ich stelle sicher, dass das Verzeichnis existiert.
            os.makedirs(dir_path, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(content) if content is not None else "")
        logger.debug(f"Datei geschrieben: {path}")

    def read(self, path: str) -> str:
        """
        Liest den Inhalt einer Textdatei und gibt ihn als String zurück.
        Wirft eine FileNotFoundError, wenn die Datei nicht existiert.

        Args:
            path (str): Pfad zur Datei.
        Returns:
            str: Inhalt der Datei als String.
        """
        logger.debug(f"Lese Datei: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.debug(f"Datei nicht gefunden beim Lesen: {path}")
            raise
        except Exception as e:
            logger.debug(f"Fehler beim Lesen der Datei {path}: {e}")
            return ""  # Gibt im Fehlerfall einen leeren String zurück

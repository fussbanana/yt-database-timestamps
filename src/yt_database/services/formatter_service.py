# src/yt_database/services/formatter_service.py
"""
FormatterService

Dieses Modul stellt einen Service bereit, der YouTube-Transkripte und Metadaten parst, bereinigt und in menschenlesbare Formate umwandelt.
Features:
- Entfernt Füllwörter aus Transkripten
- Wandelt Zeitstempel in Sekunden und HH:MM:SS um
- Vereinheitlicht Metadaten für die Datenbank
- Erstellt formatierte Textausgaben für die weitere Verarbeitung
"""

import json
from typing import Any

from loguru import logger

from yt_database.models.models import TranscriptData
from yt_database.services.protocols import FormatterServiceProtocol


class FormatterService(FormatterServiceProtocol):
    """
    Service zum Parsen und Formatieren von Transkripten und Metadaten.
    Implementiert das FormatterServiceProtocol.
    """

    def __init__(self) -> None:
        """
        Initialisiert den FormatterService und loggt die Initialisierung.
        """
        logger.debug("FormatterService initialisiert.")

    def parse_json3_transcript(self, file_path: str) -> list[dict[str, Any]]:
        """Parst eine von yt-dlp heruntergeladene .json3-Datei und filtert Füllwörter.

        Args:
            file_path (str): Pfad zur json3-Datei.

        Returns:
            list[dict[str, Any]]: Liste von Transkript-Abschnitten mit Text, Startzeit und Dauer.

        Raises:
            FileNotFoundError: Falls die Datei nicht existiert.
            Exception: Bei Fehlern im JSON-Parsing.

        Example:
            >>> service = FormatterService()
            >>> service.parse_json3_transcript("transcript.json3")
        """
        logger.debug(f"Starte Parsing der json3-Datei: {file_path}")
        try:
            # Öffne die Transkriptdatei und lade das JSON
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            events = data.get("events", [])  # Hole alle Events
            transcript = []  # Initialisiere die Ergebnisliste
            fuellwoerter = {"ähm", "mhm", "äh", "hm", "hmm", "öhm", "ah", "uh", "ähhh", "ööhm"}  # Set der Füllwörter
            for event in events:
                # Prüfe, ob Segmente vorhanden sind
                if "segs" not in event:
                    continue
                # Extrahiere die Textsegmente
                text_segments = [seg.get("utf8", "") for seg in event["segs"]]
                cleaned_text = " ".join("".join(text_segments).split())  # Entferne doppelte Leerzeichen
                # Filtere Füllwörter aus dem Text
                cleaned_text = " ".join([w for w in cleaned_text.split() if w.lower() not in fuellwoerter])
                if cleaned_text:
                    # Berechne Start- und Endzeit in Sekunden
                    start_ms = event.get("tStartMs")
                    duration_ms = event.get("dDurationMs")
                    start_sec = float(start_ms) / 1000 if start_ms is not None else 0.0
                    duration_sec = float(duration_ms) / 1000 if duration_ms is not None else 0.0
                    end_sec = start_sec + duration_sec
                    # Füge den bereinigten Abschnitt zur Ergebnisliste hinzu
                    transcript.append(
                        {
                            "text": cleaned_text,
                            "start": start_sec,
                            "end": end_sec,
                            "duration": duration_sec,
                            "start_hms": self.format_seconds_to_hms(start_sec),
                            "end_hms": self.format_seconds_to_hms(end_sec),
                            "duration_hms": self.format_seconds_to_hms(duration_sec),
                            "speaker": event.get("speaker", ""),
                        }
                    )
            logger.debug(f"Parsing abgeschlossen, {len(transcript)} Abschnitte gefunden.")
            return transcript
        except FileNotFoundError:
            logger.debug(f"Konnte die Transkript-Datei nicht finden: {file_path}")
            return []
        except Exception as e:
            logger.debug(f"Fehler beim Parsen der json3-Datei {file_path}: {e}")
            return []

    def format(self, transcript_data: "TranscriptData") -> str:
        """
        Formatiert die vollständige TranscriptData als menschenlesbaren Text im gewünschten Format.

        Args:
            transcript_data (TranscriptData): Die vollständige Datenstruktur.

        Returns:
            str: Formatierter Text mit Metadaten, Kapiteln und Transkript.

        Example:
            >>> service = FormatterService()
            >>> service.format(transcript_data)
        """
        logger.debug("Formatiere TranscriptData...")
        # Initialisiere die Zeilenliste für die Textausgabe
        lines = ["---", "Metadaten", "---"]
        meta_dict = transcript_data.model_dump()
        # Nur erlaubte Felder serialisieren
        allowed_fields = [
            "title",
            "video_id",
            "video_url",
            "channel_name",
            "channel_url",
            "channel_handle",
            "publish_date",
            "duration",
            "error_reason",
        ]
        for field in allowed_fields:
            value = meta_dict.get(field, "")
            # Fehlerfeld als 'error' statt 'error_reason' schreiben
            if field == "error_reason":
                lines.append(f"error: {value}")
            else:
                lines.append(f"{field}: {value}")

        # Kapitel-Block
        lines.append("")
        lines.append("## Kapitel mit Zeitstempeln")
        if transcript_data.chapters:
            # Füge alle Kapitel mit Zeitstempeln hinzu
            for chapter in transcript_data.chapters:
                lines.append(f"- {chapter.title} ({chapter.start_hms} - {chapter.end_hms})")
        else:
            lines.append("Keine Kapitel vorhanden.")

        # Transkript-Block
        lines.append("")
        lines.append("## Transkript\n")
        for entry in transcript_data.entries:
            # Füge jeden Transkriptabschnitt mit Sprecher und Zeit hinzu
            speaker = f"[{entry.speaker}] " if entry.speaker else ""
            lines.append(f"[{entry.start_hms}] {speaker}{entry.text}")
        if transcript_data.error_reason:
            # Fehlerhinweis am Ende
            lines.append(f"\n**Fehler:** {transcript_data.error_reason}")

        logger.debug("Formatierung abgeschlossen.")
        return "\n".join(lines)

    def extract_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Extrahiert und vereinheitlicht relevante Metadaten-Felder aus dem übergebenen Dictionary.

        Args:
            metadata (dict[str, Any]): Rohes Metadaten-Dictionary.

        Returns:
            dict[str, Any]: Vereinheitlichtes Metadaten-Dictionary mit Standardwerten für fehlende Felder.

        Example:
            >>> service = FormatterService()
            >>> service.extract_metadata(metadata)
        """
        # Mapping auf die aktuelle Datenbankstruktur
        # Ich verwende get mit Fallbacks, um fehlende Felder robust abzufangen
        mapping = {
            "video_id": metadata.get("video_id", metadata.get("id", "")),
            "channel_id": metadata.get("channel_id", metadata.get("uploader_id", "")),
            "channel_name": metadata.get("channel_name", metadata.get("uploader", "")),
            "channel_url": metadata.get("channel_url", metadata.get("original_url", "")),
            "title": metadata.get("title", ""),
            "publish_date": metadata.get("publish_date", metadata.get("upload_date", "")),
            "duration": metadata.get("duration", metadata.get("duration_string", "")),
            "is_transcribed": metadata.get("is_transcribed", False),
            "has_chapters": metadata.get("has_chapters", False),
            "youtube_url": metadata.get("youtube_url", metadata.get("original_url", "")),
            "chapters_uploaded": metadata.get("chapters_uploaded", False),
        }
        # Rückgabe des vereinheitlichten Mappings
        return mapping

    @staticmethod
    def format_seconds_to_hms(seconds: float) -> str:
        """
        Wandelt Sekunden in das Format HH:MM:SS um.

        Args:
            seconds (float): Sekunden.

        Returns:
            str: Zeit im Format HH:MM:SS

        Example:
            >>> FormatterService.format_seconds_to_hms(3661)
            '01:01:01'
        """
        # Berechne Stunden, Minuten und Sekunden aus Gesamtsekunden
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        # Rückgabe als HH:MM:SS-String
        return f"{h:02}:{m:02}:{s:02}"

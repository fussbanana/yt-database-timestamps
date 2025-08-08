#!/usr/bin/env python3
"""
Migrationsskript für Kapitel aus Markdown-Dateien in die Datenbank

Dieses Skript durchsucht alle Projektordner nach Markdown-Transkriptdateien,
extrahiert vorhandene Kapitel und speichert sie in die Datenbank.

Unterstützt zwei Kapitelformate:
1. YouTube-Kommentar-Format (unter "## Kapitel mit Zeitstempeln")
2. Detailliertes Format (unter "## Detaillierte Kapitel")

Usage:
    python scripts/migrate_chapters_to_database.py [--dry-run] [--project-path PATH]
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Füge src-Verzeichnis zum Python-Pfad hinzu
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

from loguru import logger
from peewee import DoesNotExist
from yt_database.config.settings import settings
from yt_database.database import Chapter, Transcript, db, initialize_database
from yt_database.models.models import ChapterEntry


def ensure_database_ready():
    """Stellt sicher, dass die Datenbank und FTS5-Trigger korrekt initialisiert sind."""
    try:
        # Führe die Datenbank-Initialisierung aus (inkl. FTS5-Setup)
        initialize_database()
        logger.debug("Datenbank-Initialisierung abgeschlossen.")
    except Exception as e:
        logger.warning(f"Fehler bei Datenbank-Initialisierung: {e}")


class ChapterMigrator:
    """
    Migriert Kapitel aus Markdown-Dateien in die Datenbank.
    """

    def __init__(self, project_path: str, dry_run: bool = False):
        """
        Initialisiert den ChapterMigrator.

        Args:
            project_path (str): Pfad zum Projektverzeichnis
            dry_run (bool): Wenn True, werden keine Änderungen an der Datenbank vorgenommen
        """
        # Stelle sicher, dass die Datenbank korrekt initialisiert ist
        ensure_database_ready()

        self.project_path = Path(project_path)
        self.dry_run = dry_run
        self.stats = {
            "files_processed": 0,
            "files_with_chapters": 0,
            "youtube_chapters_migrated": 0,
            "detailed_chapters_migrated": 0,
            "errors": 0
        }

    def migrate_all_chapters(self) -> None:
        """
        Startet die Migration aller Kapitel.
        """
        logger.info(f"Starte Kapitel-Migration in: {self.project_path}")
        if self.dry_run:
            logger.info("DRY-RUN Modus aktiv - keine Datenbankänderungen")

        if not self.project_path.exists():
            logger.error(f"Projektpfad existiert nicht: {self.project_path}")
            return

        # Durchsuche alle Markdown-Dateien
        markdown_files = list(self.project_path.rglob("*_transcript.md"))
        logger.info(f"Gefunden: {len(markdown_files)} Transkript-Dateien")

        for markdown_file in markdown_files:
            try:
                self._process_markdown_file(markdown_file)
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von {markdown_file}: {e}")
                self.stats["errors"] += 1

        self._print_migration_summary()

    def _process_markdown_file(self, markdown_file: Path) -> None:
        """
        Verarbeitet eine einzelne Markdown-Datei.

        Args:
            markdown_file (Path): Pfad zur Markdown-Datei
        """
        self.stats["files_processed"] += 1
        logger.debug(f"Verarbeite: {markdown_file}")

        # Extrahiere video_id aus Dateiname oder Pfad
        video_id = self._extract_video_id_from_path(markdown_file)
        if not video_id:
            logger.warning(f"Konnte video_id nicht aus Pfad extrahieren: {markdown_file}")
            return

        # Prüfe ob Transcript in Datenbank existiert
        try:
            transcript = Transcript.get(Transcript.video_id == video_id)
        except DoesNotExist:
            logger.warning(f"Transcript nicht in Datenbank gefunden: {video_id}")
            return

        # Lese Markdown-Datei
        try:
            content = markdown_file.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Fehler beim Lesen der Datei {markdown_file}: {e}")
            return

        # Extrahiere Kapitel aus beiden Formaten
        youtube_chapters = self._extract_chapters_from_content(content, "## Kapitel mit Zeitstempeln")
        detailed_chapters = self._extract_chapters_from_content(content, "## Detaillierte Kapitel")

        has_chapters = False

        # Migriere YouTube-Kommentar Kapitel
        if youtube_chapters:
            has_chapters = True
            self.stats["files_with_chapters"] += 1
            logger.info(f"{video_id}: {len(youtube_chapters)} YouTube-Kapitel gefunden")

            if not self.dry_run:
                self._save_chapters_to_database(video_id, youtube_chapters, "summary")
            self.stats["youtube_chapters_migrated"] += len(youtube_chapters)

        # Migriere detaillierte Kapitel
        if detailed_chapters:
            has_chapters = True
            if not youtube_chapters:  # Nur zählen wenn nicht bereits gezählt
                self.stats["files_with_chapters"] += 1
            logger.info(f"{video_id}: {len(detailed_chapters)} detaillierte Kapitel gefunden")

            if not self.dry_run:
                self._save_chapters_to_database(video_id, detailed_chapters, "detailed")
            self.stats["detailed_chapters_migrated"] += len(detailed_chapters)

        if not has_chapters:
            logger.debug(f"{video_id}: Keine Kapitel gefunden")

    def _extract_video_id_from_path(self, markdown_file: Path) -> Optional[str]:
        """
        Extrahiert die video_id aus dem Dateipfad.

        Args:
            markdown_file (Path): Pfad zur Markdown-Datei

        Returns:
            Optional[str]: Die video_id oder None
        """
        # Versuche video_id aus Ordnername zu extrahieren (z.B. /projects/@channel/VIDEO_ID/file.md)
        parts = markdown_file.parts
        for i, part in enumerate(parts):
            if part.startswith('@') and i + 1 < len(parts):
                potential_video_id = parts[i + 1]
                # YouTube video IDs sind 11 Zeichen lang
                if len(potential_video_id) == 11:
                    return potential_video_id

        # Fallback: Versuche aus Dateiname zu extrahieren
        filename = markdown_file.stem
        if "_transcript" in filename:
            # Entferne "_transcript" und andere bekannte Suffixe
            potential_id = filename.replace("_transcript", "").split("_")[0]
            if len(potential_id) == 11:
                return potential_id

        return None

    def _extract_chapters_from_content(self, content: str, section_header: str) -> List[ChapterEntry]:
        """
        Extrahiert Kapitel aus einem spezifischen Abschnitt der Markdown-Datei.

        Args:
            content (str): Inhalt der Markdown-Datei
            section_header (str): Header des Kapitel-Abschnitts

        Returns:
            List[ChapterEntry]: Liste der extrahierten Kapitel
        """
        # Finde den Abschnitt
        section_start = content.find(section_header)
        if section_start == -1:
            return []

        # Finde das Ende des Abschnitts (nächster ## Header oder Ende der Datei)
        section_content = content[section_start + len(section_header):]
        next_header = section_content.find("\n##")
        if next_header != -1:
            section_content = section_content[:next_header]

        # Extrahiere nur den Code-Block-Inhalt (zwischen ``` Markierungen)
        code_blocks = re.findall(r"```\n(.*?)\n```", section_content, re.DOTALL)
        if not code_blocks:
            return []

        chapter_text = code_blocks[0]  # Nimm den ersten Code-Block
        return self._parse_chapters_from_text(chapter_text)

    def _parse_chapters_from_text(self, chapter_text: str) -> List[ChapterEntry]:
        """
        Parst Kapiteltext zu strukturierten ChapterEntry-Objekten.
        Verwendet die gleiche Logik wie ChapterGenerationWorker.

        Args:
            chapter_text (str): Roher Kapiteltext

        Returns:
            List[ChapterEntry]: Liste von ChapterEntry-Objekten
        """
        chapters = []
        current_main_chapter = None

        # Split in Zeilen und filtere relevante Zeilen
        lines = chapter_text.strip().split("\n")

        for line in lines:
            line = line.strip()

            if not line or line.startswith("---") or line.startswith("```"):
                continue

            # Hauptkapitel erkennen (• ohne Zeitstempel am Anfang)
            if line.startswith("•") and ":" not in line[:20]:
                current_main_chapter = line[1:].strip()
                logger.debug(f"Erkanntes Hauptkapitel: {current_main_chapter}")
                continue

            # Unterkapitel mit Zeitstempel erkennen
            # Format: • 00:01:16: Titel oder    • 00:01:16: Titel (mit Einrückung)
            timestamp_pattern = r"^\s*•\s*(\d{1,2}:\d{2}:\d{2}):\s*(.+)"
            match = re.match(timestamp_pattern, line)

            if match:
                timestamp_str = match.group(1)
                title = match.group(2).strip()

                # Füge Hauptkapitel-Kontext hinzu wenn vorhanden
                if current_main_chapter:
                    full_title = f"{current_main_chapter} - {title}"
                else:
                    full_title = title

                try:
                    start_time = self._parse_timestamp(timestamp_str)

                    chapter = ChapterEntry(
                        title=full_title,
                        start=start_time,
                        end=0.0,  # Wird später berechnet
                        start_hms=timestamp_str,
                        end_hms="00:00:00",
                    )
                    chapters.append(chapter)
                    logger.debug(f"Kapitel hinzugefügt: {timestamp_str} - {full_title}")

                except Exception as e:
                    logger.warning(f"Fehler beim Parsen von Zeitstempel '{timestamp_str}': {e}")
                    continue

        # End-Zeiten berechnen
        for i, chapter in enumerate(chapters):
            if i < len(chapters) - 1:
                chapter.end = chapters[i + 1].start
                chapter.end_hms = self._seconds_to_hms(chapter.end)
            else:
                # Letztes Kapitel: Setze eine Standard-Endzeit oder lasse offen
                chapter.end = chapter.start + 300.0  # +5 Minuten als Standard
                chapter.end_hms = self._seconds_to_hms(chapter.end)

        return chapters

    def _parse_timestamp(self, timestamp: str) -> float:
        """
        Konvertiert Timestamp-String zu Sekunden.

        Args:
            timestamp (str): Zeitstempel als String

        Returns:
            float: Zeit in Sekunden
        """
        try:
            timestamp = timestamp.strip()
            parts = timestamp.split(":")

            if len(parts) == 3:  # HH:MM:SS
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                return hours * 3600 + minutes * 60 + seconds

            elif len(parts) == 2:  # MM:SS
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds

            else:
                logger.warning(f"Unbekanntes Zeitstempel-Format: {timestamp}")
                return 0.0

        except (ValueError, IndexError) as e:
            logger.warning(f"Fehler beim Parsen von Zeitstempel '{timestamp}': {e}")
            return 0.0

    def _seconds_to_hms(self, seconds: float) -> str:
        """Konvertiert Sekunden zu HH:MM:SS Format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _save_chapters_to_database(self, video_id: str, chapters: List[ChapterEntry], chapter_type: str) -> None:
        """
        Speichert Kapitel in die Datenbank.

        Args:
            video_id (str): Die video_id
            chapters (List[ChapterEntry]): Liste von Kapiteln
            chapter_type (str): Typ der Kapitel ("summary" oder "detailed")
        """
        try:
            with db.atomic():
                # Hole das Transcript-Objekt
                transcript_obj = Transcript.get(Transcript.video_id == video_id)

                # Lösche existierende Kapitel dieses Typs für dieses Transcript
                Chapter.delete().where(
                    (Chapter.transcript == transcript_obj) &
                    (Chapter.chapter_type == chapter_type)
                ).execute()

                # Speichere neue Kapitel
                for chapter in chapters:
                    Chapter.create(
                        transcript=transcript_obj,
                        title=chapter.title,
                        start_seconds=int(chapter.start),
                        chapter_type=chapter_type,
                    )

                # Aktualisiere Transcript-Flags
                chapter_count = len(chapters)
                if chapter_type == "summary":
                    Transcript.update(has_chapters=True, chapter_count=chapter_count).where(
                        Transcript.video_id == video_id
                    ).execute()
                    logger.debug(f"{video_id}: {chapter_count} YouTube-Kapitel in DB gespeichert")
                else:
                    Transcript.update(has_chapters=True, detailed_chapter_count=chapter_count).where(
                        Transcript.video_id == video_id
                    ).execute()
                    logger.debug(f"{video_id}: {chapter_count} detaillierte Kapitel in DB gespeichert")

        except Exception as e:
            logger.error(f"Fehler beim Speichern der Kapitel für {video_id}: {e}")
            raise

    def _print_migration_summary(self) -> None:
        """
        Druckt eine Zusammenfassung der Migration.
        """
        logger.info("\n" + "="*60)
        logger.info("MIGRATION ABGESCHLOSSEN")
        logger.info("="*60)
        logger.info(f"Dateien verarbeitet: {self.stats['files_processed']}")
        logger.info(f"Dateien mit Kapiteln: {self.stats['files_with_chapters']}")
        logger.info(f"YouTube-Kapitel migriert: {self.stats['youtube_chapters_migrated']}")
        logger.info(f"Detaillierte Kapitel migriert: {self.stats['detailed_chapters_migrated']}")
        logger.info(f"Fehler: {self.stats['errors']}")
        logger.info("="*60)


def main():
    """
    Hauptfunktion für das Migrationsskript.
    """
    parser = argparse.ArgumentParser(
        description="Migriert Kapitel aus Markdown-Dateien in die Datenbank"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Führt eine Simulation durch ohne Datenbankänderungen"
    )
    parser.add_argument(
        "--project-path",
        type=str,
        default=None,
        help="Pfad zum Projektverzeichnis (Standard: aus settings.project_path)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Aktiviert detaillierte Ausgaben"
    )

    args = parser.parse_args()

    # Konfiguriere Logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    # Bestimme Projektpfad
    project_path = args.project_path or settings.project_path
    if not project_path:
        logger.error("Kein Projektpfad angegeben. Verwende --project-path oder konfiguriere settings.project_path")
        sys.exit(1)

    # Starte Migration
    migrator = ChapterMigrator(project_path, dry_run=args.dry_run)
    migrator.migrate_all_chapters()


if __name__ == "__main__":
    main()

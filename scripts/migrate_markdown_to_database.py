#!/usr/bin/env python3
"""
Migrationsskript zum Import von Markdown-Dateien in die Datenbank.

Dieses Skript parst Metadaten und Kapitel aus Markdown-Dateien und
schreibt sie in die transcript-zentrierte Datenbankstruktur.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from loguru import logger
from peewee import IntegrityError, Model, CharField, DateTimeField, ForeignKeyField, IntegerField, BooleanField
from yt_database.config.settings import settings

# Füge das src-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Importiere die DB-Modelle mit der korrekten Benennung
from yt_database.database import Channel, Transcript, Chapter, db, initialize_database
from yt_database.models.models import ChapterEntry


class MarkdownMigrator:
    """Migriert Markdown-Dateien aus dem projects-Ordner in die Datenbank."""

    def __init__(self, projects_dir: Path, force: bool = False):
        """
        Initialisiert den Migrator.

        Args:
            projects_dir: Pfad zum Verzeichnis mit den Markdown-Dateien.
            force: Wenn True, werden existierende Kapitel überschrieben.
        """
        self.projects_dir = projects_dir
        self.force = force
        self.stats = {
            "processed_files": 0,
            "transcripts_created": 0,
            "transcripts_updated": 0,
            "chapters_created": 0,
            "chapters_skipped": 0,
            "errors": 0,
        }
        # Stelle sicher, dass die Datenbank und FTS5-Trigger korrekt initialisiert sind
        initialize_database()

    def migrate_all(self) -> None:
        """Migriert alle gefundenen Markdown-Dateien."""
        logger.info(f"Starte Migration aus {self.projects_dir}")
        markdown_files = list(self.projects_dir.rglob("*.md"))
        logger.info(f"Gefunden: {len(markdown_files)} Markdown-Dateien")

        for md_file in markdown_files:
            try:
                self._migrate_file(md_file)
            except Exception as e:
                logger.error(f"Unerwarteter Fehler bei Migration von {md_file}: {e}", exc_info=True)
                self.stats["errors"] += 1
        self._print_stats()

    def _migrate_file(self, md_file: Path) -> None:
        """Migriert eine einzelne Markdown-Datei."""
        logger.info(f"Verarbeite: {md_file}")
        content = md_file.read_text(encoding="utf-8")
        metadata = self._parse_metadata(content)

        if not metadata or not metadata.get("video_id"):
            logger.warning(f"Keine validen Metadaten in {md_file} gefunden. Überspringe.")
            return

        self.stats["processed_files"] += 1
        video_id = metadata["video_id"]

        with db.atomic():
            self._ensure_transcript_exists(metadata)

            summary_chapters = self._parse_chapter_block(content, "## Kapitel mit Zeitstempeln")
            detailed_chapters = self._parse_chapter_block(content, "## Detaillierte Kapitel")

            if summary_chapters:
                self._save_chapters(video_id, summary_chapters, "summary")
            if detailed_chapters:
                self._save_chapters(video_id, detailed_chapters, "detailed")

            has_transcript_text = self._has_transcript_content(content)
            transcript_lines_count = self._count_transcript_lines(content) if has_transcript_text else 0
            total_chapters = len(summary_chapters) + len(detailed_chapters)
            self._update_transcript_status(video_id, has_transcript_text, total_chapters, transcript_lines_count)

    def _parse_metadata(self, content: str) -> Optional[Dict]:
        """Extrahiert und repariert Metadaten aus dem YAML-Frontmatter. Ergänzt channel_id aus channel_url, falls nötig."""
        yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not yaml_match:
            return None

        yaml_text = yaml_match.group(1)

        # Repariere verschiedene YAML-Probleme
        lines = yaml_text.split("\n")
        fixed_lines = []

        for line in lines:
            # Repariere channel_handle mit führendem @
            if line.strip().startswith("channel_handle:") and "@" in line and '"' not in line:
                line = re.sub(r"^(\s*channel_handle:\s*)(@[^\s\"]+)", r'\1"\2"', line)

            # Repariere title-Zeilen mit problematischen Zeichen
            if line.strip().startswith("title:"):
                # Extrahiere den Titel-Teil nach dem Doppelpunkt
                match = re.match(r"^(\s*title:\s*)(.*)", line)
                if match:
                    prefix, title_part = match.groups()
                    title_part = title_part.strip()

                    # Wenn der Titel nicht bereits in Anführungszeichen steht
                    if not (title_part.startswith('"') and title_part.endswith('"')):
                        # Escape problematische Zeichen und setze in Anführungszeichen
                        title_part = title_part.replace('"', '\\"')
                        line = f'{prefix}"{title_part}"'

            fixed_lines.append(line)

        yaml_text = "\n".join(fixed_lines)

        try:
            metadata = yaml.safe_load(yaml_text)
            if not metadata:
                return None

            # Ergänze channel_id aus channel_url, falls nötig
            if "channel_id" not in metadata or not metadata["channel_id"]:
                url = metadata.get("channel_url", "")
                match = re.search(r"(?:youtube\.com|youtu\.be)/channel/([A-Za-z0-9_-]+)", url)
                if match:
                    metadata["channel_id"] = match.group(1)

            required = ["video_id", "title", "channel_name", "channel_id"]
            if not all(field in metadata for field in required):
                logger.warning(f"Fehlende erforderliche Felder in Metadaten: {required}")
                return None

            return metadata

        except yaml.YAMLError as e:
            logger.error(f"YAML-Parse-Fehler: {e}")
            return None

    def _parse_chapter_block(self, content: str, header: str) -> List[ChapterEntry]:
        """Parst einen spezifischen Kapitelblock aus dem Markdown."""
        chapters = []
        block_regex = rf"{re.escape(header)}\s*```\n(.*?)\n```"
        match = re.search(block_regex, content, re.DOTALL)
        if not match:
            return chapters

        chapter_text = match.group(1)
        line_regex = r"^\s*•\s*(\d{1,2}:\d{2}:\d{2}):?\s*(.+)$"

        parsed_chapters = []
        for line in chapter_text.split("\n"):
            line_match = re.match(line_regex, line.strip())
            if line_match:
                start_hms, title = line_match.groups()
                parsed_chapters.append({"start_hms": start_hms.zfill(8), "title": title.strip()})

        for i, chap in enumerate(parsed_chapters):
            start_seconds = self._time_to_seconds(chap["start_hms"])
            end_seconds = 0
            if i + 1 < len(parsed_chapters):
                end_seconds = self._time_to_seconds(parsed_chapters[i + 1]["start_hms"])

            chapters.append(
                ChapterEntry(title=chap["title"], start=start_seconds, end=end_seconds, start_hms=chap["start_hms"])
            )

        logger.info(f"Geparst: {len(chapters)} Kapitel aus Block '{header}'")
        return chapters

    def _has_transcript_content(self, content: str) -> bool:
        """Prüft, ob tatsächlich Transkript-Text vorhanden ist (verbesserte Erkennung)."""
        # Versuche verschiedene Transkript-Sektionen zu finden
        patterns = [
            r"## Transkript(.+)",  # Standard-Format
            r"# Transkript(.+)",   # Alternative Überschrift
            r"## Transcript(.+)",  # Englische Variante
            r"# Transcript(.+)",   # Englische Variante
        ]

        for pattern in patterns:
            transcript_match = re.search(pattern, content, re.DOTALL)
            if transcript_match:
                transcript_content = transcript_match.group(1).strip()
                # Zähle sinnvolle Zeilen (nicht leer, nicht nur Zeitstempel)
                lines = [
                    line for line in transcript_content.split("\n")
                    if line.strip() and not line.strip().startswith("[") and not line.strip().startswith("##")
                ]
                if len(lines) > 5:  # Mindestens 5 Zeilen echten Inhalts
                    return True

        # Fallback: Suche nach typischen Transkript-Indikatoren
        transcript_indicators = [
            "transcript_lines:",  # YAML-Metadaten
            "Text:",             # Mögliche Abschnitte
            "[00:",              # Zeitstempel-Format
            "Sprecher:",         # Deutsche Transkripte
            "Speaker:",          # Englische Transkripte
        ]

        for indicator in transcript_indicators:
            if indicator in content:
                # Wenn Indikatoren gefunden werden, zähle die Textmenge
                content_lines = [line for line in content.split("\n") if line.strip()]
                if len(content_lines) > 20:  # Genug Inhalt für ein Transkript
                    return True

        return False

    def _count_transcript_lines(self, content: str) -> int:
        """Zählt die tatsächlichen Transkript-Zeilen in der Datei."""
        try:
            # Suche nach dem Transkript-Abschnitt
            transcript_match = re.search(r"## Transkript(.+)", content, re.DOTALL)
            if not transcript_match:
                return 0

            transcript_content = transcript_match.group(1).strip()
            lines = transcript_content.split("\n")

            # Zähle Zeilen mit Zeitstempel-Pattern [HH:MM:SS-HH:MM:SS]
            transcript_lines = 0
            for line in lines:
                line = line.strip()
                if line and line.startswith("[") and "]" in line and "-" in line:
                    # Pattern: [00:00:05-00:00:10] content
                    if line.count(":") >= 4:  # mindestens 2 Zeitstempel
                        transcript_lines += 1

            return transcript_lines
        except Exception as e:
            logger.warning(f"Fehler beim Zählen der Transkript-Zeilen: {e}")
            return 0

    def _ensure_transcript_exists(self, metadata: Dict) -> None:
        """Stellt sicher, dass Kanal und Transkript-Eintrag in der DB existieren oder aktualisiert werden."""
        channel, _ = Channel.get_or_create(
            channel_id=metadata["channel_id"],
            defaults={
                "name": metadata["channel_name"],
                "url": metadata.get("channel_url", ""),
                "handle": metadata.get("channel_handle", ""),
            },
        )

        duration_value = metadata.get("duration", "0:00")
        duration_str = str(duration_value)
        transcript_data = {
            "channel": channel,
            "title": metadata["title"],
            "video_url": metadata.get("video_url", ""),
            "publish_date": metadata.get("publish_date", ""),
            "duration": self._time_to_seconds(duration_str),
            "online": metadata.get("online", False),
            # "error": metadata.get("error", "")
        }

        try:
            Transcript.create(video_id=metadata["video_id"], **transcript_data)
            self.stats["transcripts_created"] += 1
            logger.info(f"Transkript-Eintrag {metadata['video_id']} erstellt.")
        except IntegrityError:
            Transcript.update(**transcript_data).where(Transcript.video_id == metadata["video_id"]).execute()
            self.stats["transcripts_updated"] += 1
            logger.debug(f"Transkript-Eintrag {metadata['video_id']} aktualisiert.")

    def _save_chapters(self, video_id: str, chapters: List[ChapterEntry], chapter_type: str) -> None:
        """Speichert eine Liste von Kapiteln eines bestimmten Typs in der Datenbank."""
        transcript = Transcript.get_or_none(Transcript.video_id == video_id)
        if not transcript:
            logger.error(f"Transkript {video_id} nicht gefunden. Kapitel können nicht gespeichert werden.")
            return

        existing_chapters = (
            Chapter.select().where((Chapter.transcript == transcript) & (Chapter.chapter_type == chapter_type)).count()
        )

        if existing_chapters > 0 and not self.force:
            logger.warning(
                f"Transkript {video_id} hat bereits {existing_chapters} '{chapter_type}' Kapitel. Überspringe. (Nutze --force)"
            )
            self.stats["chapters_skipped"] += existing_chapters
            return

        Chapter.delete().where((Chapter.transcript == transcript) & (Chapter.chapter_type == chapter_type)).execute()

        chapter_data = [
            {
                "transcript": transcript,
                "title": chap.title,
                "start_seconds": int(chap.start),
                "chapter_type": chapter_type,
            }
            for chap in chapters
        ]
        if chapter_data:
            Chapter.insert_many(chapter_data).execute()
            logger.info(f"Gespeichert: {len(chapters)} '{chapter_type}' Kapitel für Transkript {video_id}")
            self.stats["chapters_created"] += len(chapters)

    def _update_transcript_status(self, video_id: str, has_transcript_text: bool, chapter_count: int, transcript_lines_count: int = 0) -> None:
        """Aktualisiert den Status des Transkript-Eintrags nur wenn nötig (verhindert versehentliches Überschreiben)."""
        try:
            transcript = Transcript.get_or_none(Transcript.video_id == video_id)
            if not transcript:
                logger.warning(f"Transkript {video_id} nicht gefunden für Status-Update")
                return

            # Bestimme neue Werte
            new_has_chapters = chapter_count > 0

            # Aktualisiere nur wenn der neue Wert "besser" ist oder das Feld noch nicht gesetzt war
            updates = {}

            # is_transcribed: Aktualisiere nur wenn aktuell False und neuer Wert True ist
            current_transcribed = getattr(transcript, "is_transcribed", False)
            if not current_transcribed and has_transcript_text:
                updates["is_transcribed"] = True
                logger.debug(f"Setze is_transcribed=True für {video_id}")
            elif current_transcribed and not has_transcript_text:
                # Warnung wenn ein zuvor transkribiertes Video plötzlich als nicht-transkribiert erkannt wird
                logger.warning(f"Migration würde is_transcribed von True zu False setzen für {video_id} - überspringe")

            # has_chapters: Aktualisiere nur wenn aktuell False und neuer Wert True ist
            current_has_chapters = getattr(transcript, "has_chapters", False)
            if not current_has_chapters and new_has_chapters:
                updates["has_chapters"] = True
                logger.debug(f"Setze has_chapters=True für {video_id}")
            elif current_has_chapters and not new_has_chapters:
                # Warnung wenn zuvor erkannte Kapitel plötzlich nicht mehr gefunden werden
                logger.warning(f"Migration würde has_chapters von True zu False setzen für {video_id} - überspringe")

            # transcript_lines: Aktualisiere nur wenn aktuell 0 und neuer Wert > 0 ist
            current_transcript_lines = getattr(transcript, "transcript_lines", 0)
            if current_transcript_lines == 0 and transcript_lines_count > 0:
                updates["transcript_lines"] = transcript_lines_count
                logger.debug(f"Setze transcript_lines={transcript_lines_count} für {video_id}")
            elif current_transcript_lines > 0 and transcript_lines_count == 0:
                # Warnung wenn zuvor gezählte Zeilen plötzlich nicht mehr gefunden werden
                logger.warning(f"Migration würde transcript_lines von {current_transcript_lines} zu 0 setzen für {video_id} - überspringe")            # Führe Update nur aus wenn es Änderungen gibt
            if updates:
                Transcript.update(**updates).where(Transcript.video_id == video_id).execute()
                logger.info(f"Status aktualisiert für {video_id}: {updates}")
            else:
                logger.debug(f"Keine Status-Änderungen nötig für {video_id}")

        except Exception as e:
            logger.error(f"Fehler beim Status-Update für {video_id}: {e}")

    def _time_to_seconds(self, time_str: str) -> int:
        """Konvertiert Zeitstring (HH:MM:SS oder MM:SS) zu Sekunden."""
        if not isinstance(time_str, str):
            time_str = str(time_str)
        parts = list(map(int, time_str.split(":")))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        if len(parts) == 1:
            return parts[0]
        return 0

    def _print_stats(self) -> None:
        """Gibt Migrations-Statistiken aus."""
        logger.info("=== Migrations-Statistiken ===")
        logger.info(f"Verarbeitete Dateien: {self.stats['processed_files']}")
        logger.info(f"Transkript-Einträge erstellt: {self.stats['transcripts_created']}")
        logger.info(f"Transkript-Einträge aktualisiert: {self.stats['transcripts_updated']}")
        logger.info(f"Kapitel erstellt: {self.stats['chapters_created']}")
        logger.info(f"Kapitel übersprungen: {self.stats['chapters_skipped']}")
        logger.info(f"Fehler: {self.stats['errors']}")


def main():
    """Hauptfunktion für die Migration."""
    base_dir = Path(__file__).parent.parent
    projects_dir = Path(settings.project_path)

    if not projects_dir.exists():
        logger.error(f"Projects-Verzeichnis nicht gefunden: {projects_dir}")
        return 1

    migrator = MarkdownMigrator(projects_dir=projects_dir, force=False)
    migrator.migrate_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
# --- END OF FILE migrate_markdown_to_database.py ---

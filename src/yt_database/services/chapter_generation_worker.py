"""
ChapterGenerationWorker

Asynchroner Qt-Worker zur automatischen Generierung von Kapiteln aus Transkriptdateien.
Kommuniziert ausschließlich über Qt-Signale mit der GUI und Service-Layern. Die Datei ist entkoppelt und testbar.
"""

import os
from typing import TYPE_CHECKING, Optional

from loguru import logger
from PySide6.QtCore import QObject, Signal, Slot

if TYPE_CHECKING:
    pass

from yt_database.services.protocols import AnalysisPromptServiceProtocol, FileServiceProtocol, ProjectManagerProtocol


class ChapterGenerationWorker(QObject):
    """
    Worker für die automatische Kapitelgenerierung aus Transkripten mit automatischem Thread-Management.

    Args:
        video_id (str): Eindeutige Transcript-ID, die das Transkript referenziert.
        file_path (str): Absoluter Pfad zur Transkriptdatei.
        file_service (FileServiceProtocol): Service zum Lesen/Schreiben von Dateien.
        pm_service (ProjectManagerProtocol): Service zur Verwaltung des Projektstatus.
        prompt_type (str | None): Optional. Der zu verwendende Prompt-Typ. Falls None, wird der Wert aus settings.prompt_type verwendet.

    Signals:
        finished: Signal, wenn der Workflow abgeschlossen ist.
        error: Signal mit Fehlermeldung bei Fehlern.
        status_update: Signal mit Status-Text für die GUI.
        send_transcript: Signal mit Transkript-Inhalt für die Web-Automatisierung.

    Example:
        worker = ChapterGenerationWorker(
            video_id="BaW_jenozKc",
            file_path="projects/@kanal/BaW_jenozKc/titel_transcript.md",
            file_service=file_service,
            pm_service=pm_service,
            prompt_type=PromptType.YOUTUBE_COMMENT.value
        )
        worker.start()
    """

    prompt_text_changed = Signal(str)
    prompt_updated = Signal(str)  # Neues Signal für Web-Fenster
    status_update = Signal(str)
    send_transcript = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(
        self,
        video_id: str,
        file_path: str,
        file_service: FileServiceProtocol,
        pm_service: ProjectManagerProtocol,
        analysis_prompt_service: Optional[AnalysisPromptServiceProtocol] = None,
        prompt_text: str | None = None,
        prompt_type: str | None = None,
    ):
        super().__init__()
        self.video_id = video_id
        self.file_path = file_path
        self._file_service = file_service
        self._pm_service = pm_service
        self._analysis_prompt_service = analysis_prompt_service
        self._prompt_text = prompt_text  # Speichert den explizit übergebenen Prompt-Text (optional)
        self._prompt_type = prompt_type  # Speichert den Prompt-Typ für zielgerichtete Platzierung

        # Optionale Selenium-Browser-Instanz für Web-Automatisierung
        self.browser = None  # Typ: Optional[webdriver.Chrome]
        self.processing_canceled = False

        logger.debug(f"ChapterGenerationWorker initialisiert: video_id={video_id}, prompt_type={prompt_type}")

    @Slot()
    def run(self) -> None:
        """
        Startet den Kapitelgenerierungs-Workflow.

        Liest das Transkript aus der Datei und sendet es per Signal an das Web-Fenster.
        Fehler werden geloggt und per Signal gemeldet.

        Raises:
            Exception: Wenn das Transkript nicht gelesen werden kann.

        Example:
            worker.run()
        """
        logger.debug(f"Kapitel-Workflow wird gestartet für: {self.file_path}")
        self.status_update.emit(f"Starte Kapitel-Workflow für {os.path.basename(self.file_path)}...")
        try:
            transcript_content = self._file_service.read(self.file_path)
            self.send_transcript.emit(transcript_content)
            logger.debug("Transkript erfolgreich gelesen und an Web-Fenster gesendet.")
        except Exception as e:
            logger.error(f"Fehler beim Lesen des Transkripts: {e}")
            self.error.emit(f"Fehler beim Lesen des Transkripts: {e}")
            self.finished.emit()

    @Slot(str)
    def on_chapters_extracted(self, chapter_text: str) -> None:
        """
        Verarbeitet die vom Web-Fenster extrahierten Kapitel und aktualisiert Transkriptdatei und Datenbank.

        Args:
            chapter_text (str): Extrahierter Kapiteltext.

        Raises:
            Exception: Wenn Dateioperationen fehlschlagen.

        Example:
            worker.on_chapters_extracted("Kapiteltext ...")
        """
        if not chapter_text:
            error_msg = "Kapitel-Extraktion fehlgeschlagen: Kein Text vom Web-Fenster empfangen."
            logger.error(error_msg)
            self.error.emit(error_msg)
            self.finished.emit()
            return

        self.status_update.emit("Kapitel empfangen. Aktualisiere Datei und Datenbank...")
        logger.debug(f"Kapiteltext empfangen: Aktualisiere Datei {self.file_path} und Datenbank.")
        try:
            # 1. Strukturierte Kapitel extrahieren
            try:
                chapters = self._parse_chapters_from_text(chapter_text)
                chapter_count = len(chapters)
                logger.debug(f"Erfolgreich {chapter_count} Kapitel geparst")
            except Exception as e:
                logger.warning(f"Fehler beim Parsen strukturierter Kapitel: {e}")
                chapters = []
                chapter_count = 0

            # 2. Datei aktualisieren mit Kapiteln UND Frontmatter-Anzahl
            content = self._file_service.read(self.file_path)

            # Bestimme den Placeholder basierend auf dem aktuellen Prompt-Typ
            placeholder = self._determine_chapter_placeholder()
            logger.info(f"Verwende Prompt-Typ '{self._prompt_type}', schreibe unter '{placeholder}'")

            # Füge Kapiteltext hinzu
            content_with_chapters = content.replace(placeholder, f"{placeholder}\n\n```\n{chapter_text.strip()}\n```\n")

            # Aktualisiere Frontmatter mit Kapitelanzahl
            from yt_database.utils.utils import get_or_set_frontmatter_value

            if chapter_count > 0:
                chapter_count_key = self._determine_frontmatter_chapter_key()
                _, final_content = get_or_set_frontmatter_value(
                    content_with_chapters, chapter_count_key, str(chapter_count)
                )
                # Schreibe die finalisierte Datei mit Kapiteln und aktualisiertem Frontmatter
                self._file_service.write(self.file_path, final_content)
                logger.info(
                    f"Datei aktualisiert mit {chapter_count} Kapiteln und Frontmatter-Eintrag '{chapter_count_key}: {chapter_count}'"
                )
            else:
                # Keine Kapitel gefunden, schreibe nur den Kapiteltext
                self._file_service.write(self.file_path, content_with_chapters)
                logger.warning("Keine strukturierten Kapitel gefunden, Frontmatter nicht aktualisiert")

            # 3. Kapitel in Datenbank speichern
            if chapters:
                try:
                    self._save_chapters_to_database(self.video_id, chapters)
                except Exception as e:
                    logger.warning(f"Fehler beim Speichern der Kapitel in Datenbank: {e}")
                    # Fallback: Nur das has_chapters Flag setzen

            # 3. Transcript als "mit Kapiteln" markieren
            self._pm_service.mark_as_chaptered(self.video_id)
            self.status_update.emit("Kapitel erfolgreich eingefügt und gespeichert!")
            logger.debug(f"Kapitel für Transcript {self.video_id} erfolgreich gespeichert.")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Kapitel: {e}")
            self.error.emit(f"Fehler beim Speichern der Kapitel: {e}")
        finally:
            logger.debug("Kapitel-Workflow abgeschlossen, sende 'finished'-Signal.")
            self.finished.emit()

    def _parse_chapters_from_text(self, chapter_text: str) -> list:
        """
        Parst Kapiteltext zu strukturierten ChapterEntry-Objekten.

        Unterstützt hierarchische Formate mit Haupt- und Unterkapiteln:
        • Hauptkapitel
            • 00:01:16: Unterkapitel-Titel
            • 00:02:49: Weiteres Unterkapitel

        Args:
            chapter_text: Roher Kapiteltext aus Web-Extraktion

        Returns:
            Liste von ChapterEntry-Objekten
        """
        import re

        from yt_database.models.models import ChapterEntry

        chapters = []
        current_main_chapter = None

        # Split in Zeilen und filtere relevante Zeilen
        lines = chapter_text.strip().split("\n")

        for line in lines:
            original_line = line
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

        logger.debug(f"Insgesamt {len(chapters)} Kapitel geparst.")
        return chapters

    def _parse_timestamp(self, timestamp: str) -> float:
        """
        Konvertiert Timestamp-String zu Sekunden.

        Unterstützt Formate:
        - HH:MM:SS (z.B. 00:01:16)
        - MM:SS (z.B. 01:16)

        Args:
            timestamp: Zeitstempel als String

        Returns:
            Zeit in Sekunden als float
        """
        try:
            # Entferne Leerzeichen und führende Nullen
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

    def _save_chapters_to_database(self, video_id: str, chapters: list) -> None:
        """
        Speichert die strukturierten Kapitel über den bestehenden pm_service.

        Args:
            video_id: Die Transcript-ID
            chapters: Liste von ChapterEntry-Objekten
        """
        try:
            # Nutze den bestehenden pm_service, der bereits die save_chapters-Methode haben sollte
            # Falls nicht vorhanden, implementiere direkte Datenbankoperationen
            if hasattr(self._pm_service, "save_chapters_to_database"):
                chapter_type = self._determine_chapter_type_for_database()
                self._pm_service.save_chapters_to_database(video_id, chapters, chapter_type)
            else:
                # Fallback: Direkte Datenbankoperationen
                self._save_chapters_to_database_direct(video_id, chapters)

            logger.debug(f"Erfolgreich {len(chapters)} Kapitel für Transcript {video_id} gespeichert.")

        except Exception as e:
            logger.error(f"Fehler beim Speichern der Kapitel für Transcript {video_id}: {e}")
            raise

    def _save_chapters_to_database_direct(self, video_id: str, chapters: list) -> None:
        """
        Direkte Datenbankoperationen für Kapitel-Speicherung als Fallback.

        Args:
            video_id: Die Transcript-ID
            chapters: Liste von ChapterEntry-Objekten
        """
        from yt_database.database import Chapter, Transcript, db
        from yt_database.models.models import ChapterEntry

        logger.debug(f"Speichere {len(chapters)} Kapitel für Transcript {video_id} direkt in Datenbank.")

        try:
            with db.atomic():
                # Hole das Transcript-Objekt
                transcript_obj = Transcript.get(Transcript.video_id == video_id)

                # Lösche existierende Kapitel für dieses Transcript
                Chapter.delete().where(Chapter.transcript == transcript_obj).execute()

                # Speichere neue Kapitel mit korrektem chapter_type
                chapter_type = self._determine_chapter_type_for_database()
                for i, chapter in enumerate(chapters):
                    if isinstance(chapter, ChapterEntry):
                        Chapter.create(
                            transcript=transcript_obj,
                            title=chapter.title,
                            start_seconds=int(chapter.start),
                            chapter_type=chapter_type,
                        )
                    else:
                        logger.warning(f"Kapitel {i} ist kein ChapterEntry-Objekt: {type(chapter)}")

                # Transcript als "mit Kapiteln" markieren und Anzahl aktualisieren
                chapter_count = len(chapters)
                logger.info(f"Speichere {chapter_count} Kapitel vom Typ '{chapter_type}' für Transcript {video_id}")

                # Bestimme Kapiteltyp-spezifische Update-Felder
                if chapter_type == "summary":
                    # Einfache Kapitel (YouTube-Kommentar-Format)
                    Transcript.update(has_chapters=True, chapter_count=chapter_count).where(
                        Transcript.video_id == video_id
                    ).execute()
                    logger.debug(f"Transcript als mit {chapter_count} einfachen Kapiteln markiert")
                else:
                    # Detaillierte Kapitel (Datenbank-Format)
                    Transcript.update(has_chapters=True, detailed_chapter_count=chapter_count).where(
                        Transcript.video_id == video_id
                    ).execute()
                    logger.debug(f"Transcript als mit {chapter_count} detaillierten Kapiteln markiert")

        except Exception as e:
            logger.error(f"Fehler beim direkten Speichern der Kapitel für Transcript {video_id}: {e}")
            raise

    def _determine_chapter_placeholder(self) -> str:
        """
        Bestimmt den korrekten Platzhalter für Kapitel basierend auf dem aktuellen Prompt-Typ.

        Returns:
            str: Der Platzhalter für die Kapitel-Sektion
        """
        if self._prompt_type == "youtube_comment":
            return "## Kapitel mit Zeitstempeln"
        elif self._prompt_type == "detailed_database":
            return "## Detaillierte Kapitel"
        else:
            # Fallback: Bestimme basierend auf dem Prompt-Text
            if self._prompt_text and "youtube_comment" in self._prompt_text.lower():
                return "## Kapitel mit Zeitstempeln"
            else:
                return "## Detaillierte Kapitel"

    def _determine_chapter_type_for_database(self) -> str:
        """
        Bestimmt den chapter_type für die Datenbank basierend auf dem aktuellen Prompt-Typ.

        Returns:
            str: Der chapter_type für die Datenbank ("summary" oder "detailed")
        """
        if self._prompt_type == "youtube_comment":
            return "summary"
        elif self._prompt_type == "detailed_database":
            return "detailed"
        else:
            # Fallback basierend auf Prompt-Text
            if self._prompt_text and "youtube_comment" in self._prompt_text.lower():
                return "summary"
            else:
                return "detailed"

    def _determine_frontmatter_chapter_key(self) -> str:
        """
        Bestimmt den korrekten Frontmatter-Schlüssel für die Kapitelanzahl basierend auf dem aktuellen Prompt-Typ.

        Returns:
            str: Der Frontmatter-Schlüssel für die Kapitelanzahl
        """
        if self._prompt_type == "youtube_comment":
            return "chapter_count"
        elif self._prompt_type == "detailed_database":
            return "detailed_chapter_count"
        else:
            # Fallback basierend auf Prompt-Text
            if self._prompt_text and "youtube_comment" in self._prompt_text.lower():
                return "chapter_count"
            else:
                return "detailed_chapter_count"

    @Slot(str)
    def on_automation_failed(self, error_message: str) -> None:
        """
        Behandelt Fehler, die von der Web-Automatisierung gemeldet werden.

        Args:
            error_message (str): Fehlermeldung vom Web-Fenster.

        Example:
            worker.on_automation_failed("Timeout beim Extrahieren")
        """
        logger.error(f"Automatisierungsfehler vom Web-Fenster empfangen: {error_message}")
        self.error.emit(f"Web-Automatisierung fehlgeschlagen: {error_message}")
        self.finished.emit()

    def stop_worker(self) -> None:
        """
        Beendet den zugehörigen Thread sauber, falls er noch läuft.
        Diese Methode sollte vor dem Schließen der Anwendung oder beim Abbruch aufgerufen werden.
        """
        thread = self.thread()
        if thread and thread.isRunning():
            logger.debug("Beende BatchTranscriptionWorker-Thread sauber.")
            thread.quit()
            thread.wait(1000)

    @Slot(str)
    def on_prompt_text_changed(self, prompt_text: str) -> None:
        """
        Slot zum dynamischen Aktualisieren des Prompt-Texts während der Laufzeit.

        Args:
            prompt_text (str): Der neue Prompt-Text.
        """
        logger.debug(f"Prompt-Text dynamisch im Worker geändert: {prompt_text}")
        self._prompt_text = prompt_text

    @Slot(str, str)
    def on_prompt_type_changed(self, prompt_type_value: str, description: str) -> None:
        """
        Slot zum dynamischen Aktualisieren des Prompt-Typs während der Laufzeit.

        Args:
            prompt_type_value (str): Der neue Prompt-Typ-Wert (z.B. "youtube_comment", "detailed_database")
            description (str): Beschreibung des Prompts
        """
        logger.info(f"Prompt-Typ dynamisch im Worker geändert: {prompt_type_value} - {description}")
        self._prompt_type = prompt_type_value

        # Aktualisiere den Prompt-Text, falls AnalysisPromptService verfügbar ist
        if self._analysis_prompt_service:
            try:
                from yt_database.services.analysis_prompt_service import PromptType

                if prompt_type_value == "youtube_comment":
                    new_prompt_type = PromptType.YOUTUBE_COMMENT
                elif prompt_type_value == "detailed_database":
                    new_prompt_type = PromptType.DETAILED_DATABASE
                else:
                    logger.warning(f"Unbekannter Prompt-Typ: {prompt_type_value}")
                    return

                self._prompt_text = self._analysis_prompt_service.get_prompt(new_prompt_type)
                logger.debug(f"Prompt-Text für Typ '{prompt_type_value}' aktualisiert")

                # Informiere das Web-Fenster über den neuen Prompt
                self.prompt_updated.emit(self._prompt_text)

            except Exception as e:
                logger.error(f"Fehler beim Aktualisieren des Prompt-Texts: {e}")

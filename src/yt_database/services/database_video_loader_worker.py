# src/yt_database/services/database_video_loader_worker.py
"""
Worker-Klasse für das asynchrone Laden von Videos aus der Datenbank.

Diese Klasse lädt alle Videos aus der Datenbank in einem separaten Thread,
um die GUI-Responsivität zu gewährleisten.
"""

import os
import time
from typing import Any, List, Optional

from loguru import logger
from PySide6.QtCore import QObject, Signal

from yt_database.database import Transcript
from yt_database.services.protocols import ProjectManagerProtocol


class DatabaseVideoLoaderWorker(QObject):
    """
    Worker-Klasse für das asynchrone Laden von Videos aus der Datenbank.

    Signals:
        finished: Emittiert, wenn das Laden erfolgreich abgeschlossen wurde.
        error: Emittiert bei Fehlern mit der Fehlermeldung.
        videos_loaded: Emittiert die geladenen Videos als Liste.
        progress: Emittiert den Fortschritt beim Laden (aktuell, gesamt).
    """

    finished = Signal()
    error = Signal(str)
    videos_loaded = Signal(list)
    progress = Signal(int, int)

    def __init__(
        self, project_manager_service: ProjectManagerProtocol, videos: Optional[List[Transcript]] = None
    ) -> None:
        """
        Initialisiert den DatabaseVideoLoaderWorker.

        Args:
            project_manager_service: Service für Datenbank-Zugriffe und Transcript-Checks.
            videos: Optional vorgefertigte Liste von Videos (um DB-Zugriff im Worker zu vermeiden).
        """
        super().__init__()
        self.pm_service = project_manager_service
        self._video_cache: dict[str, dict[str, bool | str | None]] = {}  # Cache für Transkript-Infos
        self._videos = videos  # Videos können optional übergeben werden

    def run(self) -> None:
        """
        Lädt alle Videos aus der Datenbank und überprüft deren Transkript-Status effizient.

        Diese Methode läuft im Worker-Thread und emittiert Progress-Updates
        sowie das finale Ergebnis.
        """
        try:
            logger.debug("DatabaseVideoLoaderWorker: Starte intelligentes Laden der Videos aus der Datenbank")

            # Verwende übergebene Videos oder lade sie aus der Datenbank
            if self._videos is not None:
                videos = self._videos
                logger.debug(f"DatabaseVideoLoaderWorker: {len(videos)} Videos vom Main-Thread erhalten")
            else:
                # Fallback: Lade Videos aus der Datenbank (für Kompatibilität)
                videos = self._load_videos_from_database()
                logger.debug(f"DatabaseVideoLoaderWorker: {len(videos)} Videos aus DB geladen")

            if not videos:
                logger.debug("DatabaseVideoLoaderWorker: Keine Videos in der Datenbank gefunden")
                self.videos_loaded.emit([])
                self.finished.emit()
                return

            logger.debug(f"DatabaseVideoLoaderWorker: {len(videos)} Videos aus DB geladen")

            # Effiziente Batch-Verarbeitung mit intelligentem Transcript-Check
            enriched_videos = []
            total_videos = len(videos)
            progress_batch_size = 100  # Für Progress-Updates
            video_batch_size = 50  # Für Transcript-Emissionen

            # Einmalige Sammlung aller Channel-IDs für Batch-Operationen
            channel_ids = set()
            for video in videos:
                if hasattr(video, "channel_id") and video.channel_id:
                    channel_ids.add(str(video.channel_id))

            # Batch-Check für Transcript-Verzeichnisse
            transcript_info = self._batch_check_transcript_directories(channel_ids)

            for i, video in enumerate(videos):
                try:
                    if not hasattr(video, "video_id") or not video.video_id:
                        continue

                    # Intelligenter Transcript-Check mit vorher gesammelten Informationen
                    enriched_video = self._create_enriched_video_with_batch_info(video, transcript_info)
                    enriched_videos.append(enriched_video)

                except Exception as e:
                    logger.debug(
                        f"DatabaseVideoLoaderWorker: Fehler bei Transcript {getattr(video, 'video_id', 'unknown')}: {e}"
                    )
                    continue

                # Progress-Updates nur alle 100 Videos oder am Ende
                if (i + 1) % progress_batch_size == 0 or (i + 1) == total_videos:
                    self.progress.emit(i + 1, total_videos)

            logger.debug(f"DatabaseVideoLoaderWorker: {len(enriched_videos)} Videos erfolgreich verarbeitet")

            # Übertrage Videos in kleineren Batches, um Threading-Probleme zu vermeiden
            for i in range(0, len(enriched_videos), video_batch_size):
                batch = enriched_videos[i : i + video_batch_size]
                self.videos_loaded.emit(batch)

                # Kleine Pause zwischen Batches um Thread-Stress zu reduzieren
                time.sleep(0.02)  # 20ms Pause für stabilere GUI-Updates

            logger.debug("DatabaseVideoLoaderWorker: Alle Transcript-Batches erfolgreich emittiert")
            self.finished.emit()

        except Exception as e:
            error_msg = f"Fehler beim Laden der Videos aus der Datenbank: {e}"
            logger.error(f"DatabaseVideoLoaderWorker: {error_msg}")
            self.error.emit(error_msg)

    def _load_videos_from_database(self) -> List[Transcript]:
        """
        Lädt alle Videos aus der Datenbank.

        Returns:
            Liste aller Transcript-Objekte aus der Datenbank.

        Raises:
            Exception: Bei Datenbankfehlern wird die Exception weitergegeben.
        """
        # Thread-safe Database-Operation: Erstelle neue Verbindung für Thread
        try:
            from yt_database.database import db

            # Stelle sicher, dass die Datenbankverbindung für diesen Thread initialisiert ist
            if db.is_closed():
                db.connect()

            # Alle Videos aus der Datenbank laden (ohne Channel-Filter)
            videos = list(Transcript.select())
            return videos
        except Exception as e:
            logger.error(f"Datenbankfehler beim Laden der Videos: {e}")
            raise

    def _enrich_video_with_transcript_status(self, video: Transcript) -> Any:
        """
        Erweitert ein Transcript-Objekt mit aktuellen Transkript-Status-Informationen.

        Args:
            video: Transcript-Objekt aus der Datenbank.

        Returns:
            Erweitertes Transcript-Objekt mit aktuellen Status-Informationen.
        """
        try:
            # Prüfe ob das Transcript eine gültige Kanal-ID hat
            if not video.channel_id:
                # Videos ohne Kanal-ID haben definitionsgemäß keine Transkripte
                return {"video": video, "has_transcript": False, "has_chapters": False, "transcript_path": None}

            # Verwende Cache für Transcript-ID um wiederholte Service-Aufrufe zu vermeiden
            video_id_str = str(video.video_id)
            if video_id_str in self._video_cache:
                cached_result = self._video_cache[video_id_str]
                return {
                    "video": video,
                    "has_transcript": cached_result["has_transcript"],
                    "has_chapters": cached_result["has_chapters"],
                    "transcript_path": cached_result["transcript_path"],
                }

            # Einmaliger Aufruf für Transcript-Pfad (um doppelte Aufrufe zu vermeiden)
            transcript_path = self.pm_service.get_transcript_path_for_video_id(video_id_str)
            has_transcript = transcript_path and os.path.exists(transcript_path)

            # Chapter-Status nur prüfen, wenn Transkript existiert
            has_chapters = False
            if has_transcript and transcript_path:
                has_chapters = self._check_chapter_status_from_file(transcript_path)

            # Cache das Ergebnis
            self._video_cache[video_id_str] = {
                "has_transcript": has_transcript,
                "has_chapters": has_chapters,
                "transcript_path": transcript_path if has_transcript else None,
            }

            # Erstelle erweiterte Transcript-Information (als Dict für einfache Handhabung)
            enriched_video = {
                "video": video,
                "has_transcript": has_transcript,
                "has_chapters": has_chapters,
                "transcript_path": transcript_path if has_transcript else None,
            }

            return enriched_video

        except Exception as e:
            logger.warning(f"DatabaseVideoLoaderWorker: Fehler beim Erweitern von Transcript {video.video_id}: {e}")
            # Fallback: Verwende DB-Werte oder sichere Defaults
            return {
                "video": video,
                "has_transcript": getattr(video, "is_transcribed", False),
                "has_chapters": getattr(video, "has_chapters", False),
                "transcript_path": None,
            }

    def _batch_check_transcript_directories(self, channel_ids: set) -> dict:
        """
        Überprüft effizient alle Transcript-Verzeichnisse für die gegebenen Channel-IDs.

        Args:
            channel_ids: Set der Channel-IDs zum Überprüfen.

        Returns:
            Dict mit Channel-ID als Key und Set der verfügbaren Transcript-IDs als Value.
        """
        transcript_info = {}

        try:
            # Hole projects_dir vom ProjectManager
            projects_dir = getattr(self.pm_service, "projects_dir", "./projects")

            for channel_id in channel_ids:
                try:
                    channel_dir = os.path.join(projects_dir, str(channel_id))
                    video_ids_with_transcripts = set()

                    if os.path.exists(channel_dir) and os.path.isdir(channel_dir):
                        # Durchsuche alle Unterverzeichnisse nach Transcript-Dateien
                        for video_dir in os.listdir(channel_dir):
                            video_path = os.path.join(channel_dir, video_dir)
                            if os.path.isdir(video_path):
                                transcript_file = os.path.join(video_path, f"{video_dir}_transcript.md")
                                if os.path.exists(transcript_file):
                                    video_ids_with_transcripts.add(video_dir)

                    transcript_info[str(channel_id)] = video_ids_with_transcripts

                except Exception as e:
                    logger.debug(f"Fehler beim Batch-Check für Channel {channel_id}: {e}")
                    transcript_info[str(channel_id)] = set()

        except Exception as e:
            logger.warning(f"Fehler beim Batch-Check der Transcript-Verzeichnisse: {e}")

        return transcript_info

    def _create_enriched_video_with_batch_info(self, video, transcript_info: dict) -> dict:
        """
        Erstellt ein erweitertes Transcript-Objekt mit Batch-Informationen.

        Args:
            video: Transcript-Objekt aus der Datenbank.
            transcript_info: Vorher gesammelte Transcript-Informationen.

        Returns:
            Erweitertes Transcript-Objekt.
        """
        try:
            video_id = str(video.video_id)
            channel_id = str(video.channel_id) if video.channel_id else None

            # Transcript-Status aus Batch-Informationen ermitteln
            has_transcript = False
            if channel_id and channel_id in transcript_info:
                has_transcript = video_id in transcript_info[channel_id]

            # Chapter-Check nur wenn Transcript vorhanden
            has_chapters = False
            transcript_path = None

            if has_transcript and channel_id:
                try:
                    projects_dir = getattr(self.pm_service, "projects_dir", "./projects")
                    transcript_path = os.path.join(projects_dir, channel_id, video_id, f"{video_id}_transcript.md")
                    if os.path.exists(transcript_path):
                        has_chapters = self._check_chapter_status_from_file(transcript_path)
                except Exception:
                    pass  # Ignore chapter check errors

            return {
                "video": video,
                "has_transcript": has_transcript,
                "has_chapters": has_chapters,
                "transcript_path": transcript_path,
            }

        except Exception as e:
            logger.warning(
                f"Fehler beim Erstellen der erweiterten Transcript-Info für {getattr(video, 'video_id', 'unknown')}: {e}"
            )
            # Fallback zu DB-Werten
            return {
                "video": video,
                "has_transcript": getattr(video, "is_transcribed", False),
                "has_chapters": getattr(video, "has_chapters", False),
                "transcript_path": None,
            }

    def _check_chapter_status_from_file(self, transcript_path: str) -> bool:
        """
        Überprüft, ob in einer Transkript-Datei Kapitel vorhanden sind.

        Args:
            transcript_path: Pfad zur Transkript-Datei.

        Returns:
            True wenn Kapitel vorhanden sind, False sonst.
        """
        try:
            if not transcript_path or not os.path.exists(transcript_path):
                return False

            with open(transcript_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Einfache Heuristik: Suche nach Kapitel-Markierungen
                return "## Kapitel" in content or "# Kapitel" in content or "chapters:" in content.lower()

        except Exception as e:
            logger.warning(f"DatabaseVideoLoaderWorker: Fehler beim Chapter-Check für Datei {transcript_path}: {e}")
            return False

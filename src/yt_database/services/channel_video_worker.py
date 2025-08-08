# src/yt_database/services/channel_video_worker.py
"""
Worker-Klasse für das asynchrone Laden von Channel-Transcripts.

Diese Klasse kapselt die Logik zum Laden von Transcripts für einen Channel,
entweder aus der Datenbank oder neu vom TranscriptService.
Sie läuft in einem eigenen Thread, um die GUI nicht zu blockieren.
"""

import os
from typing import Any, List

from loguru import logger
from PySide6.QtCore import QObject, Signal

from yt_database.database import Channel
from yt_database.models.models import TranscriptData, TranscriptEntry
from yt_database.services.protocols import (
    ProjectManagerProtocol,
)


class ChannelVideoWorker(QObject):
    """Worker-Klasse für das asynchrone Laden von Channel-Transcripts.

    Signals:
        finished: Emittiert, wenn das Laden erfolgreich abgeschlossen wurde.
        error: Emittiert bei Fehlern mit der Fehlermeldung.
        videos_loaded: Emittiert die geladenen Transcripts als Liste.
    """

    finished = Signal()
    error = Signal(str)
    videos_loaded = Signal(list)
    transcribed_videos_found = Signal(list)

    def __init__(
        self,
        service_factory: Any,
        channel_url: str,
        force_download: bool = False,
    ) -> None:
        """Initialisiert den ChannelVideoWorker.

        Args:
            service_factory: Factory für Service-Instanzen.
            channel_url: URL des Channels.
            force_download: Ob ein Force-Download durchgeführt werden soll.
        """
        super().__init__()
        self.service_factory = service_factory
        self.channel_url = channel_url
        self.force_download = force_download

    def run(self) -> None:
        """Führt das Laden der Channel-Transcripts aus.

        Diese Methode läuft im Worker-Thread und lädt die Transcripts
        entweder aus der Datenbank oder neu vom TranscriptService.
        """
        try:
            logger.debug(f"ChannelVideoWorker: Starte Laden für Channel: {self.channel_url}")

            transcripts = []

            if self.force_download:
                # Force-Download aktiv → Immer neue Transcripts vom TranscriptService laden
                logger.debug("ChannelVideoWorker: Force-Download aktiv - lade Transcripts vom TranscriptService")
                transcripts = self._fetch_videos_from_service()
            else:
                # Checkbox inaktiv → Erst versuchen aus DB zu laden
                transcripts = self._try_load_from_db_or_service()

            logger.debug(f"ChannelVideoWorker: Insgesamt {len(transcripts)} Transcripts geladen")

            # Emittiere die geladenen Transcripts
            self.videos_loaded.emit(transcripts)
            # Signalisiere erfolgreichen Abschluss
            self.finished.emit()

        except Exception as e:
            error_msg = f"Fehler beim Laden der Channel-Transcripts: {e}"
            logger.error(f"ChannelVideoWorker: {error_msg}")
            self.error.emit(error_msg)

    def _fetch_videos_from_service(self) -> List[TranscriptData]:
        """Lädt Transcripts direkt vom TranscriptService.

        Returns:
            Liste der geladenen TranscriptData-Objekte.
        """
        transcript_service = self.service_factory.get_transcript_service()
        return transcript_service.fetch_channel_metadata(self.channel_url)

    def _try_load_from_db_or_service(self) -> List[TranscriptData]:
        """Versucht Transcripts aus der DB zu laden, fallback zum TranscriptService.

        Returns:
            Liste der geladenen TranscriptData-Objekte.
        """
        try:
            pm_service = self.service_factory.get_project_manager_service()

            # Versuche Channel anhand der URL in der DB zu finden

            channel = Channel.select().where(Channel.url == self.channel_url).first()

            if channel:
                # Channel gefunden → Transcripts aus DB laden
                db_videos = pm_service.get_videos_for_channel(channel.channel_id)

                if db_videos:
                    logger.debug(f"ChannelVideoWorker: Transcripts aus Datenbank geladen: {len(db_videos)}")
                    return self._convert_db_videos_to_transcript_data(db_videos, channel, pm_service)
                else:
                    logger.debug(
                        "ChannelVideoWorker: Keine Transcripts für Channel in DB gefunden - lade vom TranscriptService"
                    )
                    return self._fetch_videos_from_service()
            else:
                # Channel nicht in DB → Lade vom TranscriptService
                logger.debug("ChannelVideoWorker: Channel nicht in DB gefunden - lade vom TranscriptService")
                return self._fetch_videos_from_service()

        except Exception as db_error:
            logger.warning(f"ChannelVideoWorker: DB-Zugriff fehlgeschlagen: {db_error} - lade vom TranscriptService")
            return self._fetch_videos_from_service()

    def _convert_db_videos_to_transcript_data(
        self, db_videos: List, channel, pm_service: ProjectManagerProtocol
    ) -> List[TranscriptData]:
        """
        Konvertiert DB-Transcript-Objekte zu TranscriptData-Objekten.

        Args:
            db_videos: Liste der Transcript-Objekte aus der Datenbank.
            channel: Channel-Objekt aus der Datenbank.
            pm_service: ProjectManager-Service für Transcript-Pfad-Checks.

        Returns:
            Liste der konvertierten TranscriptData-Objekte.
        """
        transcripts = []
        transcribed_ids = []
        for transcript in db_videos:
            # Prüfe ob Transkript vorhanden ist (per Dateisystem-Check)
            transcript_path = pm_service.get_transcript_path_for_video_id(transcript.video_id)
            has_transcript = transcript_path and os.path.exists(transcript_path)

            # Sammle die Transcript-IDs mit Transkript
            if has_transcript:
                transcribed_ids.append(transcript.video_id)

            # Erstelle TranscriptData aus Transcript-Datenbank-Objekt
            transcript_data = TranscriptData(
                video_id=transcript.video_id,
                title=transcript.title,
                channel_id=str(transcript.channel.channel_id),
                channel_name=str(transcript.channel.name),
                channel_url=str(transcript.channel.url),
                video_url=str(transcript.video_url),
                publish_date=str(transcript.publish_date or ""),
                duration="",  # Duration nicht in Transcript-Tabelle verfügbar
                # Entries: Dummy-Entry wenn Transkript existiert, sonst leer
                entries=[TranscriptEntry(text="[Transkript vorhanden]", start=0.0, end=0.0)] if has_transcript else [],
                # error_reason=transcript.error_reason,
            )
            transcripts.append(transcript_data)

        # Sende die IDs mit Transkript an den Hauptthread
        if transcribed_ids:
            self.transcribed_videos_found.emit(transcribed_ids)

        return transcripts

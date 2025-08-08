"""
BatchTranscriptionService
Service zur automatisierten Batch-Transkription von YouTube-Videos eines Kanals.
Verarbeitet eine Liste von Transcript-IDs, steuert den Fortschritt und synchronisiert Transkripte.
"""

import time
from typing import Callable, Optional

from loguru import logger

# from yt_database.services.protocols import (
# GeneratorServiceProtocol,
# ProjectManagerProtocol,
# )
from yt_database.services.service_factory import ServiceFactory


# from yt_database.services.generator_service import GeneratorServiceProtocol
class BatchTranscriptionService:
    """
    Service für die automatisierte Batch-Transkription von YouTube-Videos.

    Args:
        service_factory (ServiceFactory): Zentrale Factory für alle Services.
        interval_seconds (int): Wartezeit zwischen Transkriptionen.
        max_videos (Optional[int]): Maximale Anzahl zu verarbeitender Videos.
    """

    def __init__(
        self,
        service_factory: "ServiceFactory",
        interval_seconds: int,
        max_videos: Optional[int],
    ) -> None:
        """
        Initialisiert den BatchTranscriptionService mit zentraler ServiceFactory.

        Args:
            service_factory (ServiceFactory): Zentrale Factory für alle Services.
            interval_seconds (int): Wartezeit zwischen Transkriptionen.
            max_videos (Optional[int]): Maximale Anzahl zu verarbeitender Videos.
        """
        self.service_factory = service_factory
        self.interval_seconds = interval_seconds
        self.max_videos = max_videos
        # self.project_manager_service: ProjectManagerProtocol = service_factory.get_project_manager_service()
        self.generator_service = self.service_factory.get_generator_service()
        logger.debug(
            f"BatchTranscriptionService initialisiert mit Intervall {interval_seconds}s und max_videos={max_videos} (Factory)"
        )

    def run_batch_transcription(
        self,
        channel_url: str,
        video_ids_to_process: Optional[list[str]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        logger.info(f"Starte Batch-Transkription für Kanal: {channel_url}")

        # Schritt 1: Bestimme die Liste der zu verarbeitenden Videos.
        if video_ids_to_process is not None:
            remaining_ids = video_ids_to_process
            logger.info(f"Verarbeite {len(remaining_ids)} spezifisch ausgewählte Videos für Kanal '{channel_url}'.")
        else:
            logger.error("Es wurden keine Transcript-IDs zur Verarbeitung übergeben. Abbruch.")
            return

        if not remaining_ids:
            logger.info("Keine neuen Videos zur Transkription vorhanden.")
            return

        # Schritt 2: Iteriere über die verbleibenden Videos und rufe den GeneratorService auf.
        for idx, video_id in enumerate(remaining_ids, 1):
            logger.info(f"[{idx}/{len(remaining_ids)}] Verarbeite Transcript: {video_id}")
            try:
                # Die Metadaten werden nicht mehr benötigt, nur die Transcript-ID und der Channel-URL
                self.generator_service.run(channel_handle=channel_url, video_id=video_id)
                logger.success(f"Transkript für {video_id} erfolgreich gespeichert.")

                if progress_callback:
                    progress_callback(idx)
            except Exception as e:
                logger.error(f"Fehler bei der Verarbeitung von Transcript {video_id}: {e}")

            if idx < len(remaining_ids):
                logger.info(f"Warte {self.interval_seconds} Sekunden bis zum nächsten Transcript...")
                time.sleep(self.interval_seconds)
        logger.info("Batch-Transkription abgeschlossen.")

from typing import Any, Callable, Optional

from loguru import logger

from yt_database.services.protocols import (
    BatchTranscriptionServiceProtocol,
    GeneratorServiceProtocol,
    ProjectManagerProtocol,
)


class MockBatchTranscriptionService(BatchTranscriptionServiceProtocol):
    """Mock-Service für die Batch-Transkription von YouTube-Videos eines Kanals.

    Simuliert das Verhalten des echten BatchTranscriptionService für Tests.
    Die Signatur entspricht exakt dem Protokoll, damit die Factory und Typisierung funktionieren.
    """

    called_with: list[Any]
    last_channel_url: Optional[str]
    called: bool

    def __init__(
        self,
        interval_seconds: int,
        max_videos: Optional[int],
        project_manager_service: ProjectManagerProtocol,
        generator_service: GeneratorServiceProtocol,
    ) -> None:
        """Initialisiert den Mock-BatchTranscriptionService.

        Args:
            interval_seconds (int): Intervall zwischen den Transkriptionen.
            max_videos (Optional[int]): Maximale Anzahl der Videos.
            project_manager_service (ProjectManagerProtocol): Mock für das Projektmanagement.
            generator_service (GeneratorServiceProtocol): Mock für die Generierung.
        """
        self.interval_seconds = interval_seconds
        self.max_videos = max_videos
        self.project_manager_service = project_manager_service
        self.generator_service = generator_service
        self.called_with = []
        self.last_channel_url = None
        self.called = False

    def run_batch_transcription(
        self,
        channel_url: str,
        video_ids_to_process: Optional[list[str]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        """Simuliert die Batch-Transkription für einen Kanal.

        Args:
            channel_url (str): Die YouTube-Kanal-URL.
            video_ids_to_process (Optional[list[str]]): Optionale Liste von Transcript-IDs.
        """
        logger.info(f"[MOCK] Starte Batch-Transkription für Kanal: {channel_url}")
        self.called_with.append((channel_url, video_ids_to_process, self.interval_seconds, self.max_videos))
        self.last_channel_url = channel_url
        self.called = True
        logger.info("[MOCK] Batch-Transkription abgeschlossen.")

    def run(self, channel_url: str) -> None:
        """Kompatibilitätsmethode für Factory/Protokoll."""
        self.run_batch_transcription(channel_url)

"""
SingleTranscriptionService

Service zur Orchestrierung der Einzeltranskription eines YouTube-Videos.
"""

from loguru import logger

from yt_database.models.models import TranscriptData
from yt_database.services.protocols import (
    FileServiceProtocol,
    FormatterServiceProtocol,
    ProjectManagerProtocol,
    TranscriptServiceProtocol,
)


class SingleTranscriptionService:
    """Orchestriert den gesamten Prozess der Einzeltranskription."""

    def __init__(
        self,
        transcript_service: TranscriptServiceProtocol,
        formatter_service: FormatterServiceProtocol,
        file_service: FileServiceProtocol,
        project_manager: ProjectManagerProtocol,
    ):
        self.transcript_service = transcript_service
        self.formatter_service = formatter_service
        self.file_service = file_service
        self.project_manager = project_manager

    def process_video(self, transcript_data: TranscriptData) -> TranscriptData:
        """
        Führt den kompletten Workflow für ein einzelnes Video aus.

        Args:
            transcript_data (TranscriptData): Die initialen Daten des Videos.

        Returns:
            TranscriptData: Das aktualisierte Datenobjekt nach der Verarbeitung.
        """
        logger.info(f"Starte Verarbeitung für Video: {transcript_data.video_id}")

        # 1. Transkript abrufen
        fetched_transcript_data = self.transcript_service.fetch_transcript(transcript_data.video_id)
        if fetched_transcript_data.error_reason:
            logger.warning(
                f"Verarbeitung für {transcript_data.video_id} abgebrochen. Grund: {fetched_transcript_data.error_reason}"
            )
            return fetched_transcript_data

        if not fetched_transcript_data.entries:
            msg = "Transkript ist leer oder nicht vorhanden."
            logger.warning(f"Verarbeitung für {transcript_data.video_id} abgebrochen. Grund: {msg}")
            fetched_transcript_data.error_reason = msg
            return fetched_transcript_data

        logger.success(
            f"Gültiges Transkript mit {len(fetched_transcript_data.entries)} Zeilen für {fetched_transcript_data.video_id} gefunden."
        )

        # 2. Transkriptdatei schreiben
        self.file_service.write_transcript_file(fetched_transcript_data)
        logger.info(f"Transkriptdatei für {fetched_transcript_data.video_id} geschrieben.")

        # 3. Datenbank-Index wird bereits vom FileService aktualisiert
        # (siehe FileService._update_transcript_database_status)

        return fetched_transcript_data

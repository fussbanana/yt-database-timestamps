"""
MockGeneratorService für Tests und Factory.

Simuliert den Transkriptions-Workflow ohne echte Dateizugriffe oder API-Aufrufe.
Alle Aufrufe werden protokolliert.
"""

from loguru import logger


class MockGeneratorService:
    def run(self, channel_handle: str, video_id: str) -> None:
        # Dummy-Methode für Protokoll-Kompatibilität
        pass

    """
    Mock-Service für den vollständigen Transkriptions-Workflow eines einzelnen YouTube-Videos.

    :param project_manager: Mock für ProjectManagerService
    :param transcript_service: Mock für TranscriptService
    :param formatter_service: Mock für FormatterService
    :param file_service: Mock für FileService
    :param metadata_service: Mock für YoutubeMetadataService
    """

    def __init__(
        self,
        project_manager,
        transcript_service,
        formatter_service,
        file_service,
        metadata_service,
    ):
        logger.debug("MockGeneratorService initialisiert.")
        self.project_manager = project_manager
        self.transcript_service = transcript_service
        self.formatter_service = formatter_service
        self.file_service = file_service
        self.metadata_service = metadata_service
        self.calls = []  # Speichert alle run-Transcript-IDs

    def run_workflow(self, id: str, video_id: str) -> None:
        """
        Simuliert den Transkriptions-Workflow. Speichert den Aufruf und loggt das Verhalten.
        """
        logger.info(f"[MOCK] Starte Verarbeitung für Transcript: {video_id} (Channel: {id})")
        self.calls.append((id, video_id))
        if self.metadata_service:
            metadata = self.metadata_service.fetch_video_metadata(video_id)
            metadata = dict(metadata)
            metadata["id"] = id
        else:
            metadata = {"id": id}
        if self.project_manager:
            self.project_manager.create_project(id, video_id)
        if self.transcript_service:
            result = self.transcript_service.fetch_transcript(video_id)
            transcript = result.get("transcript") or {}
        else:
            transcript = {}
        if self.formatter_service:
            formatted = self.formatter_service.format(transcript, metadata)
        else:
            formatted = str(transcript)
        if self.file_service:
            self.file_service.write(f"mock_{video_id}_transcript.txt", formatted)
        if self.project_manager:
            self.project_manager.update_index(video_id, dict(metadata))
        logger.info(f"[MOCK] Verarbeitung für Transcript {video_id} abgeschlossen.")

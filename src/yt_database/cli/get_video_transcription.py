import argparse

from loguru import logger

from yt_database.gui.web_view_window import WebEngineWindow
from yt_database.services.batch_transcription_service import BatchTranscriptionService
from yt_database.services.batch_transcription_worker import BatchTranscriptionWorker
from yt_database.services.chapter_generation_worker import ChapterGenerationWorker
from yt_database.services.file_service import FileService
from yt_database.services.formatter_service import FormatterService
from yt_database.services.generator_service import GeneratorService
from yt_database.services.metadata_formatter import MetadataFormatter
from yt_database.services.project_manager_service import ProjectManagerService
from yt_database.services.selector_service import SelectorService
from yt_database.services.service_factory import ServiceFactory
from yt_database.services.single_transcription_worker import SingleTranscriptionWorker
from yt_database.services.transcript_service import TranscriptService
from yt_database.services.web_automation_service import WebAutomationService


def get_video_transcription_main() -> None:
    """
    Extrahiert Transkript und Metadaten für ein einzelnes YouTube-Transcript und speichert sie strukturiert ab.

    Diese Funktion kapselt den gesamten Workflow über den GeneratorService und speichert die Ergebnisse
    im Projektverzeichnis.

    Beispiel:
        >>> $ poetry run python run.py transcribe-video "BaW_jenozKc" "@99ZUEINS"

    Args:
        Keine (CLI-Argumente werden automatisch geparst).

    Raises:
        Exception: Bei Fehlern im Transkriptions-Workflow.
    """
    logger.info("get-video-transcription CLI gestartet.")
    parser = argparse.ArgumentParser(
        description="Extrahiert Transkript und Metadaten für ein einzelnes YouTube-Transcript."
    )
    parser.add_argument("video_id", help="ID des YouTube-Videos")
    parser.add_argument("channel_id", help="Channel-Name mit @ (z.B. @99ZUEINS)")
    args = parser.parse_args()
    logger.info(f"Starte Workflow für Transcript-ID: {args.video_id}, Channel-ID: {args.channel_id}")

    from typing import Mapping

    transcript_providers: Mapping[str, type] = {
        "api": TranscriptService,
        "yt_dlp": TranscriptService,
    }
    service_factory = ServiceFactory(
        file_service_class=FileService,
        formatter_service_class=FormatterService,
        metadata_formatter_class=MetadataFormatter,
        project_manager_class=ProjectManagerService,
        generator_service_class=GeneratorService,
        batch_transcription_service_class=BatchTranscriptionService,
        batch_transcription_worker_class=BatchTranscriptionWorker,
        chapter_generation_worker_class=ChapterGenerationWorker,
        selector_service_class=SelectorService,
        web_automation_service_class=WebAutomationService,
        web_engine_window_class=WebEngineWindow,
        transcript_service_classes=transcript_providers,
        single_transcription_worker_class=SingleTranscriptionWorker,
    )
    service = service_factory.get_generator_service()
    service.run(args.channel_id, args.video_id)


if __name__ == "__main__":
    get_video_transcription_main()

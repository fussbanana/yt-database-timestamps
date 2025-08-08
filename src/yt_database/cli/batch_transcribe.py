"""
CLI-Tool zur Batch-Transkription aller Videos eines YouTube-Kanals.

Dieses Skript kann direkt über die Kommandozeile ausgeführt werden und nutzt die ServiceFactory,
um für einen angegebenen Kanal alle Videos zu transkribieren.

Beispiel:
    poetry run python -m yt_database.cli.batch_transcribe \
        https://www.youtube.com/@kanalname --interval 30 --max 10

Optionen:
    channel_url   URL des YouTube-Kanals (Pflichtargument)
    --interval    Wartezeit zwischen Videos in Sekunden (Standard: 60)
    --max         Maximale Anzahl Videos (optional)
"""

# src/yt_database/cli/batch_transcribe.py
import argparse

from loguru import logger

from yt_database.gui.web_view_window import WebEngineWindow
from yt_database.services.batch_transcription_service import (
    BatchTranscriptionService,
)
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


def batch_transcribe_main() -> None:
    """
    Startet die Batch-Transkription für einen YouTube-Kanal über die Kommandozeile.

    Führt alle Transkriptionsschritte für alle Videos eines Kanals aus.

    Beispiel:
        poetry run python -m yt_database.cli.batch_transcribe \
            https://www.youtube.com/@kanalname --interval 30 --max 10

    :raises SystemExit: Bei fehlerhafter Argumentübergabe.
    """
    parser = argparse.ArgumentParser(description="Batch-Transkription für alle Videos eines YouTube-Kanals.")
    parser.add_argument("channel_url", help="URL des YouTube-Kanals")
    parser.add_argument("--interval", type=int, default=10, help="Wartezeit zwischen Videos (Sekunden)")
    parser.add_argument("--max", type=int, default=None, help="Maximale Anzahl Videos (optional)")
    args = parser.parse_args()

    logger.info("Starte Batch-Transkription über CLI...")

    from typing import Mapping

    transcript_providers: Mapping[str, type] = {
        "api": TranscriptService,
        "yt_dlp": TranscriptService,
    }
    factory = ServiceFactory(
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
    service = factory.get_batch_transcription_service(interval_seconds=args.interval, max_videos=args.max)
    service.run_batch_transcription(args.channel_url)


if __name__ == "__main__":
    batch_transcribe_main()

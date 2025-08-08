"""
Zentrale Factory-Konfiguration für yt_database.
Initialisiert die ServiceFactory mit allen benötigten Klassen.
"""

from yt_database.gui.web_view_window import WebEngineWindow
from yt_database.services.analysis_prompt_service import AnalysisPromptService
from yt_database.services.batch_transcription_service import BatchTranscriptionService
from yt_database.services.batch_transcription_worker import BatchTranscriptionWorker
from yt_database.services.channel_video_worker import ChannelVideoWorker
from yt_database.services.chapter_generation_worker import ChapterGenerationWorker
from yt_database.services.file_service import FileService
from yt_database.services.formatter_service import FormatterService
from yt_database.services.generator_service import GeneratorService
from yt_database.services.metadata_formatter import MetadataFormatter
from yt_database.services.project_manager_service import ProjectManagerService
from yt_database.services.selector_service import SelectorService
from yt_database.services.service_factory import ServiceFactory
from yt_database.services.single_transcription_service import SingleTranscriptionService
from yt_database.services.single_transcription_worker import SingleTranscriptionWorker
from yt_database.services.transcript_service import TranscriptService
from yt_database.services.web_automation_service import WebAutomationService


def create_service_factory() -> ServiceFactory:
    """Erstellt und konfiguriert die zentrale ServiceFactory für das Projekt."""
    return ServiceFactory(
        transcript_service_class=TranscriptService,
        file_service_class=FileService,
        formatter_service_class=FormatterService,
        metadata_formatter_class=MetadataFormatter,
        project_manager_class=ProjectManagerService,
        generator_service_class=GeneratorService,
        batch_transcription_service_class=BatchTranscriptionService,
        selector_service_class=SelectorService,
        web_automation_service_class=WebAutomationService,
        analysis_prompt_service_class=AnalysisPromptService,
        single_transcription_service_class=SingleTranscriptionService,
        web_engine_window_class=WebEngineWindow,
        chapter_generation_worker_class=ChapterGenerationWorker,
        channel_video_worker_class=ChannelVideoWorker,
        batch_transcription_worker_class=BatchTranscriptionWorker,
        single_transcription_worker_class=SingleTranscriptionWorker,
    )

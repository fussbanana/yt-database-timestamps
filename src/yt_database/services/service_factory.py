"""
ServiceFactory: Zentrale Factory für alle Service- und Worker-Instanzen im yt_database-Projekt.

Dieses Modul kapselt die Erstellung und Verwaltung aller Services und Worker über Dependency Injection.
Singleton- und Transient-Pattern sorgen für effiziente und flexible Instanziierung.
Alle Services und Worker werden typisiert und mit ihren Abhängigkeiten versehen.

Example:
    factory = ServiceFactory(...)
    file_service = factory.get_file_service()
    worker = factory.get_batch_transcription_worker(...)
"""

from typing import Optional

from loguru import logger
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWidgets import QWidget

from yt_database.config.settings import settings
from yt_database.models.models import TranscriptData

from .protocols import (
    AnalysisPromptServiceProtocol,
    BatchTranscriptionServiceProtocol,
    FileServiceProtocol,
    FormatterServiceProtocol,
    GeneratorServiceProtocol,
    MetadataFormatterProtocol,
    ProjectManagerProtocol,
    SelectorServiceProtocol,
    SingleTranscriptionServiceProtocol,
    TranscriptServiceProtocol,
    WebAutomationServiceProtocol,
    WebEngineWindowProtocol,
)


class ServiceFactory:
    """
    Factory für die Erstellung und Verwaltung aller Service- und Worker-Instanzen.

    Args:
        **kwargs: Mapping von Klassennamen zu Implementierungen.

    Attributes:
        _classes (dict): Registry aller Klassen für Services und Worker.
        _instances (dict): Cache für Singleton-Service-Instanzen.
    """

    def __init__(self, **kwargs):
        """Initialisiert die Factory mit den Klassen für Services und Worker.

        Args:
            **kwargs: Mapping von Klassennamen zu Implementierungen.
        """
        logger.debug("Initialisiere ServiceFactory mit Klassen-Registry.")
        # Speichert alle übergebenen Klassen dynamisch
        self._classes = kwargs
        # Cache für Singleton-Service-Instanzen
        self._instances = {}
        self._single_transcription_service: Optional[SingleTranscriptionServiceProtocol] = None

    # Singleton Service Getters

    def get_file_service(self) -> FileServiceProtocol:
        """Gibt die Singleton-Instanz des FileService zurück.

        Returns:
            FileServiceProtocol: Instanz des FileService.
        """
        if "file_service" not in self._instances:
            logger.debug("Erzeuge Singleton-Instanz: FileService")
            self._instances["file_service"] = self._classes["file_service_class"](settings=settings)
        return self._instances["file_service"]

    def get_formatter_service(self) -> FormatterServiceProtocol:
        """Gibt die Singleton-Instanz des FormatterService zurück.

        Returns:
            FormatterServiceProtocol: Instanz des FormatterService.
        """
        if "formatter_service" not in self._instances:
            logger.debug("Erzeuge Singleton-Instanz: FormatterService")
            self._instances["formatter_service"] = self._classes["formatter_service_class"]()
        return self._instances["formatter_service"]

    def get_project_manager_service(self) -> ProjectManagerProtocol:
        """Gibt die Singleton-Instanz des ProjectManagerService zurück.

        Returns:
            ProjectManagerProtocol: Instanz des ProjectManagerService.
        """
        if "project_manager" not in self._instances:
            logger.debug("Erzeuge Singleton-Instanz: ProjectManagerService")
            self._instances["project_manager"] = self._classes["project_manager_class"](
                settings=settings,
                file_service=self.get_file_service(),
            )
        return self._instances["project_manager"]

    def get_selector_service(self) -> SelectorServiceProtocol:
        """Gibt die Singleton-Instanz des SelectorService zurück.

        Returns:
            SelectorServiceProtocol: Instanz des SelectorService.
        """
        if "selector_service" not in self._instances:
            logger.debug("Erzeuge Singleton-Instanz: SelectorService")
            self._instances["selector_service"] = self._classes["selector_service_class"]()
        return self._instances["selector_service"]

    def get_analysis_prompt_service(self) -> AnalysisPromptServiceProtocol:
        """Gibt die Singleton-Instanz des AnalysisPromptService zurück.

        Returns:
            AnalysisPromptServiceProtocol: Instanz des AnalysisPromptService.
        """
        if "analysis_prompt_service" not in self._instances:
            logger.debug("Erzeuge Singleton-Instanz: AnalysisPromptService")
            self._instances["analysis_prompt_service"] = self._classes["analysis_prompt_service_class"](
                settings=settings
            )
        return self._instances["analysis_prompt_service"]

    # Transient Service Getters (jedes Mal eine neue Instanz)

    def get_single_transcription_service(self) -> SingleTranscriptionServiceProtocol:
        """Gibt eine Instanz des SingleTranscriptionService zurück.

        Returns:
            SingleTranscriptionServiceProtocol: Instanz des SingleTranscriptionService.

        Raises:
            RuntimeError: Wenn die Instanz nicht erzeugt werden kann.
        """
        if self._single_transcription_service is None:
            logger.debug("Erzeuge Singleton-Instanz: SingleTranscriptionService")
            self._single_transcription_service = self._classes["single_transcription_service_class"](
                transcript_service=self.get_transcript_service(),
                formatter_service=self.get_formatter_service(),
                file_service=self.get_file_service(),
                project_manager=self.get_project_manager_service(),
            )
        if self._single_transcription_service is None:
            raise RuntimeError("SingleTranscriptionService konnte nicht erzeugt werden.")
        return self._single_transcription_service

    def get_transcript_service(self) -> TranscriptServiceProtocol:
        """
        Gibt eine neue Instanz des TranscriptService für den in den Settings konfigurierten Provider zurück.

        Returns:
            TranscriptServiceProtocol: Instanz des TranscriptService.
        Raises:
            ValueError: Wenn kein gültiger Provider konfiguriert ist.
        """
        logger.debug("Erzeuge neue Instanz: TranscriptService (YouTube-DLP)")
        # Einziger konfigurierter Provider: YouTube-DLP
        service_class = self._classes.get("transcript_service_class")
        if not service_class:
            raise ValueError("Kein Transkript-Service konfiguriert. Bitte 'transcript_service_class' setzen.")
        transcript_service = service_class(settings=settings)

        # Injiziere die Factory in den TranscriptService
        transcript_service.factory = self
        return transcript_service

    def get_generator_service(self) -> GeneratorServiceProtocol:
        """Gibt eine neue Instanz des GeneratorService für den in den Settings konfigurierten Provider zurück.

        Returns:
            GeneratorServiceProtocol: Instanz des GeneratorService.
        """
        logger.debug("Erzeuge neue Instanz: GeneratorService (Provider aus Settings)")
        return self._classes["generator_service_class"](
            self.get_project_manager_service(),
            self.get_transcript_service(),
            self.get_formatter_service(),
            self.get_file_service(),
        )

    def get_batch_transcription_service(
        self, interval_seconds: int = 60, max_videos: Optional[int] = None
    ) -> BatchTranscriptionServiceProtocol:
        """Gibt eine neue Instanz des BatchTranscriptionService zurück.

        Args:
            interval_seconds (int): Intervall in Sekunden.
            max_videos (Optional[int]): Maximale Anzahl Videos.
        Returns:
            BatchTranscriptionServiceProtocol: Instanz des BatchTranscriptionService.
        """
        logger.debug("Erzeuge neue Instanz: BatchTranscriptionService")
        batch_service_class = self._classes["batch_transcription_service_class"]
        # Prüfe, ob die Klasse wirklich BatchTranscriptionService ist
        if batch_service_class.__name__ != "BatchTranscriptionService":
            raise TypeError(
                f"batch_transcription_service_class verweist auf {batch_service_class.__name__}, erwartet wird BatchTranscriptionService!"
            )
        return batch_service_class(
            self,
            interval_seconds,
            max_videos,
        )

    def get_metadata_formatter(self) -> MetadataFormatterProtocol:
        """
        Gibt die Singleton-Instanz des MetadataFormatter zurück.

        Returns:
            MetadataFormatterProtocol: Instanz des MetadataFormatter.
        """
        if "metadata_formatter" not in self._instances:
            logger.debug("Erzeuge Singleton-Instanz: MetadataFormatter")
            self._instances["metadata_formatter"] = self._classes["metadata_formatter_class"]()
        return self._instances["metadata_formatter"]

    # UI und Worker Getters

    def get_web_automation_service(self, page: QWebEnginePage) -> WebAutomationServiceProtocol:
        """Gibt eine neue Instanz des WebAutomationService zurück.

        Args:
            page (QWebEnginePage): Die WebEnginePage-Instanz.
        Returns:
            WebAutomationServiceProtocol: Instanz des WebAutomationService.
        """
        logger.debug("Erzeuge neue Instanz: WebAutomationService")
        return self._classes["web_automation_service_class"](page=page, selectors=self.get_selector_service())

    def get_web_engine_window(self, parent: Optional[QWidget] = None) -> WebEngineWindowProtocol:
        """Gibt eine neue Instanz des WebEngineWindow zurück.

        Args:
            parent (Optional[QWidget]): Parent-Widget.
        Returns:
            WebEngineWindowProtocol: Instanz des WebEngineWindow.
        """
        logger.debug("Erzeuge neue Instanz: WebEngineWindow")
        return self._classes["web_engine_window_class"](service_factory=self, parent=parent)

    def get_batch_transcription_worker(
        self,
        channel_url: str,
        interval: int,
        provider: str,
        video_ids: list[str],
        max_videos: Optional[int] = None,
    ):
        """Erstellt einen BatchTranscriptionWorker und injiziert seine Abhängigkeiten.

        Args:
            channel_url (str): Kanal-URL.
            interval (int): Intervall in Sekunden.
            provider (str): Name des Providers.
            video_ids (list[str]): Liste der Transcript-IDs.
            max_videos (Optional[int]): Maximale Anzahl Videos.
        Returns:
            BatchTranscriptionWorkerProtocol: Instanz des Workers.
        """
        logger.debug("Erzeuge neuen BatchTranscriptionWorker mit Abhängigkeiten.")
        batch_service = self.get_batch_transcription_service(interval_seconds=interval, max_videos=max_videos)
        return self._classes["batch_transcription_worker_class"](
            channel_url=channel_url, video_ids=video_ids, batch_transcription_service=batch_service
        )

    def get_chapter_generation_worker(self, video_id: str, file_path: str):
        """Erstellt einen ChapterGenerationWorker und injiziert seine Abhängigkeiten.

        Args:
            video_id (str): Transcript-ID.
            file_path (str): Pfad zur Transkriptdatei.
        Returns:
            ChapterGenerationWorkerProtocol: Instanz des Workers.
        """
        logger.debug("Erzeuge neuen ChapterGenerationWorker mit Abhängigkeiten.")
        return self._classes["chapter_generation_worker_class"](
            video_id=video_id,
            file_path=file_path,
            file_service=self.get_file_service(),
            pm_service=self.get_project_manager_service(),
        )

    def get_single_transcription_worker(self, transcript_data: TranscriptData):
        """
        Erstellt einen SingleTranscriptionWorker und injiziert seine Abhängigkeiten.
        """
        logger.debug("Erzeuge neuen SingleTranscriptionWorker mit Abhängigkeiten.")
        service = self.get_single_transcription_service()
        return self._classes["single_transcription_worker_class"](
            transcript_data=transcript_data, single_transcription_service=service
        )

    def get_generator_worker(self, channel_handle: str, video_id: str):
        """
        Gibt eine neue Instanz des GeneratorWorker zurück.

        Args:
            channel_handle (str): Handle des YouTube-Kanals.
            video_id (str): ID des YouTube-Videos.

        Returns:
            GeneratorWorker: Instanz des Workers.
        """

        return self._classes["generator_worker_class"](
            channel_handle=channel_handle, video_id=video_id, generator_service=self.get_generator_service()
        )

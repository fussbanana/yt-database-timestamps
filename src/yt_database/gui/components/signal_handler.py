# src/yt_database/gui/prototype/signal_handler.py

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QObject, Slot

from yt_database.config.settings import settings
from yt_database.gui.web_view_window import WebEngineWindow
from yt_database.services.batch_transcription_worker import BatchTranscriptionWorker
from yt_database.services.channel_video_worker import ChannelVideoWorker
from yt_database.services.chapter_generation_worker import ChapterGenerationWorker

if TYPE_CHECKING:
    from yt_database.gui.main_window import MainWindow
    from yt_database.gui.web_view_window import WebEngineWindow
    from yt_database.gui.components.worker_manager import WorkerManager
    from yt_database.services.batch_transcription_worker import BatchTranscriptionWorker
    from yt_database.services.channel_video_worker import ChannelVideoWorker
    from yt_database.services.chapter_generation_worker import ChapterGenerationWorker
    from yt_database.services.service_factory import ServiceFactory


class SignalHandler(QObject):
    """Handles signals from the main window's widgets."""

    def __init__(self, main_window: MainWindow, service_factory: ServiceFactory, worker_manager: WorkerManager):
        super().__init__()
        self.main_window = main_window
        self.service_factory = service_factory
        self.worker_manager = worker_manager
        # Entferne fehlerhafte Typanmerkungen für dynamische MainWindow-Attribute
        # Die Typanmerkungen für dynamische Attribute sind entfernt, um Kompilierungsfehler zu vermeiden.
        # self.main_window.stack: QStackedWidget

    def connect_signals(self):
        """Connects all signals to the appropriate slots."""

        # Globale Aktionen
        self.main_window.notebook_action.triggered.connect(self.main_window.show_notebook_lm_window)

        # Navigation
        self.main_window.sidebar.dashboard_requested.connect(lambda: self.main_window.stack.setCurrentIndex(0))
        self.main_window.sidebar.database_requested.connect(lambda: self.main_window.stack.setCurrentIndex(1))
        self.main_window.sidebar.transcripts_requested.connect(lambda: self.main_window.stack.setCurrentIndex(2))
        self.main_window.sidebar.search_requested.connect(lambda: self.main_window.stack.setCurrentIndex(3))
        self.main_window.sidebar.log_requested.connect(lambda: self.main_window.stack.setCurrentIndex(4))
        self.main_window.sidebar.text_editor_requested.connect(lambda: self.main_window.stack.setCurrentIndex(5))

        # Dashboard
        self.main_window.dashboard_widget.quick_batch_transcription_requested.connect(
            self._on_quick_batch_transcription
        )
        self.main_window.dashboard_widget.quick_database_refresh_requested.connect(self._on_quick_database_refresh)
        self.main_window.dashboard_widget.quick_settings_requested.connect(self._on_quick_settings)
        self.main_window.dashboard_widget.channel_analysis_requested.connect(self._on_channel_analysis)

        # Batch Transcription
        self.main_window.batch_transcription_widget.channel_videos_requested.connect(self._start_channel_videos_worker)
        self.main_window.batch_transcription_widget.batch_transcription_requested.connect(
            self._start_batch_transcription_worker
        )
        self.main_window.batch_transcription_widget.file_open_requested.connect(self._on_database_file_open_requested)
        self.main_window.batch_transcription_widget.chapter_generation_requested.connect(
            self._start_chapter_generation_worker
        )
        self.main_window.batch_transcription_widget.text_editor_open_requested.connect(
            self._show_transcript_in_text_editor
        )

        # Database
        self.main_window.database_widget.chapter_generation_requested.connect(self._start_chapter_generation_worker)
        self.main_window.database_widget.file_open_requested.connect(self._on_database_file_open_requested)
        self.main_window.database_widget.text_editor_open_requested.connect(self._show_transcript_in_text_editor)
        self.main_window.database_widget.single_transcription_requested.connect(self._start_single_transcription_worker)
        self.main_window.database_widget.batch_transcription_requested.connect(
            self._start_batch_transcription_from_database
        )

        # Search
        self.main_window.search_widget.search_requested.connect(self._perform_search)

        # Config Dialog
        self.main_window.config_dialog.settingsSaved.connect(self._on_settings_saved)
        self.main_window.config_dialog.dialogCancelled.connect(self._on_config_dialog_cancelled)

        # Toolbar Actions
        self.main_window.settings_toolbar_action.triggered.connect(self._on_settings_toolbar_clicked)

        # Explorer
        self.main_window.explorer_widget.file_selected.connect(self._show_file_in_text_editor)
        self.main_window.explorer_widget.folder_selected.connect(self._on_folder_selected)
        self.main_window.explorer_widget.chapter_generation_requested.connect(
            lambda path: self._start_chapter_generation_worker(path)
        )

        # Transcript Selection Table
        self.main_window.batch_transcription_widget.video_selection_table.prompt_text_changed.connect(
            self.on_prompt_text_changed
        )
        self.main_window.batch_transcription_widget.video_selection_table.prompt_text_changed.connect(
            self.on_prompt_text_changed
        )

        # Log Widget
        self.main_window.log_message_received.connect(self.main_window.log_widget.receive_log)

    @Slot()
    def _start_channel_videos_worker(self) -> None:
        """Starts the ChannelVideoWorker."""
        logger.info("Channel transcripts requested - starting worker.")
        channel_url_input = getattr(self.main_window.batch_transcription_widget, "channel_url_input", None)
        force_download = self.main_window.batch_transcription_widget.force_metadata

        if not channel_url_input or not hasattr(channel_url_input, "text"):
            logger.warning("Channel URL input not found.")
            return

        url = channel_url_input.text().strip()

        if not url:
            logger.warning("No channel URL entered.")
            return
        logger.info(f"Starting ChannelVideoWorker for: {url}")

        self.main_window.dashboard_widget.set_progress("Loading channel transcripts...", -1)

        # Start the worker via WorkerManager
        def connect_worker_signals(worker):
            worker.transcribed_videos_found.connect(self._on_transcribed_videos_found)
            worker.videos_loaded.connect(self._on_videos_loaded)

        self.worker_manager.start_worker(
            task_name="channel_videos_fetch",
            worker_factory=lambda: ChannelVideoWorker(
                service_factory=self.service_factory, channel_url=url, force_download=force_download
            ),
            on_finish=self._on_worker_finished,
            on_error=self._on_worker_error,
            additional_signal_connections=connect_worker_signals,
        )

    @Slot(list)
    def _on_transcribed_videos_found(self, video_ids: list) -> None:
        """Slot: Setzt is_transcribed=True für alle empfangenen Transcript-IDs im Hauptthread.
        Prüft auch, ob Transcript-Dateien existieren und setzt transcript_lines entsprechend.

        Args:
            video_ids (list): Liste der Transcript-IDs mit vorhandenem Transkript.
        """
        logger.info(f"Setze is_transcribed=True für Transcripts: {video_ids}")
        from yt_database.database import Transcript as DBVideo

        pm_service = self.service_factory.get_project_manager_service()

        for vid in video_ids:
            # Prüfe ob Transcript-Datei existiert und zähle Zeilen
            transcript_path = pm_service.get_transcript_path_for_video_id(vid)
            transcript_lines = 0

            if transcript_path and os.path.exists(transcript_path):
                try:
                    with open(transcript_path, "r", encoding="utf-8") as f:
                        transcript_lines = sum(1 for line in f if line.strip())
                    logger.debug(f"Transcript-Datei für {vid} gefunden mit {transcript_lines} Zeilen")
                except Exception as e:
                    logger.warning(f"Fehler beim Lesen der Transcript-Datei für {vid}: {e}")

            # Update sowohl is_transcribed als auch transcript_lines
            DBVideo.update(is_transcribed=True, transcript_lines=transcript_lines).where(
                DBVideo.video_id == vid
            ).execute()

            logger.debug(f"Video {vid}: is_transcribed=True, transcript_lines={transcript_lines} gesetzt")

    @Slot(list)
    def _on_videos_loaded(self, video_data: list) -> None:
        """Slot: Empfängt geladene Videodaten und leitet sie an das BatchTranscriptionWidget weiter.

        Args:
            video_data (list): Liste der TranscriptData-Objekte.
        """
        logger.info(f"Videos vom Worker erhalten: {len(video_data)} Videos")

        # Leite die Videos an das BatchTranscriptionWidget weiter
        if hasattr(self.main_window, "batch_transcription_widget"):
            self.main_window.batch_transcription_widget.on_videos_loaded(video_data)
            logger.debug("Videos an BatchTranscriptionWidget weitergeleitet")
        else:
            logger.warning("BatchTranscriptionWidget nicht gefunden - Videos können nicht angezeigt werden")

    @Slot()
    def _start_batch_transcription_worker(self) -> None:
        """Starts the BatchTranscriptionWorker."""
        logger.info("Batch transcription requested - starting worker.")
        channel_url_input = getattr(self.main_window.batch_transcription_widget, "channel_url_input", None)
        if not channel_url_input or not hasattr(channel_url_input, "text"):
            logger.warning("Channel URL input not found.")
            return
        url = channel_url_input.text().strip()
        if not url:
            logger.warning("No channel URL entered.")
            return

        video_ids = self.main_window.batch_transcription_widget.get_selected_video_ids()
        if not video_ids:
            logger.warning("No videos selected for batch transcription.")
            return

        # Hole den ProjectManagerService
        pm_service = self.service_factory.get_project_manager_service()

        # Erstelle die Liste der TranscriptData-Objekte
        transcript_data_list = pm_service.create_transcript_data_for_batch(channel_url=url, video_ids=video_ids)

        if not transcript_data_list:
            logger.error("Could not create transcript data for batch. Aborting.")
            return

        logger.info(f"Starting batch transcription for: {url}")
        self.main_window.dashboard_widget.set_progress("Batch transcription running...", -1)
        self.worker_manager.start_worker(
            task_name="batch_transcription",
            worker_factory=lambda: BatchTranscriptionWorker(
                transcript_data_list=transcript_data_list,
                batch_transcription_service=self.service_factory.get_batch_transcription_service(),
            ),
            on_finish=self._on_worker_finished,
            on_error=self._on_worker_error,
        )

    @Slot(str, str, bool)
    def _start_single_transcription_worker(self, video_id: str, channel_handle: str, force_download: bool) -> None:
        """Startet den SingleTranscriptionWorker für ein einzelnes Video."""
        logger.info(f"Einzeltranskription für Video {video_id} angefordert.")

        # Hole den ProjectManagerService
        pm_service = self.service_factory.get_project_manager_service()

        # Erstelle das TranscriptData-Objekt
        transcript_data = pm_service.create_transcript_data_for_single(video_id)

        if transcript_data.error_reason:
            logger.error(f"Konnte TranscriptData für Video {video_id} nicht erstellen: {transcript_data.error_reason}")
            return

        logger.info(f"Starte Einzeltranskription für Video: {video_id}")
        self.main_window.dashboard_widget.set_progress("Einzeltranskription läuft...", -1)

        self.worker_manager.start_worker(
            task_name=f"single_transcription_{video_id}",
            worker_factory=lambda: self.service_factory.get_single_transcription_worker(transcript_data),
            on_finish=self._on_single_transcription_finished,
            on_error=self._on_worker_error,
        )

    @Slot()
    def _on_single_transcription_finished(self) -> None:
        """Callback spezifisch für Single-Transcription Worker."""
        logger.info("Single-Transcription Worker finished successfully.")
        self.main_window.dashboard_widget.clear_progress()

        # UI-Update für alle Widgets
        self.main_window.ui_update_requested.emit()

        # Spezifische Updates nach Single-Transcription
        self.main_window.dashboard_widget._refresh_stats()
        if hasattr(self.main_window, "database_widget"):
            self.main_window.database_widget.reload_videos_in_table()
            logger.info("Database Widget nach Single-Transcription aktualisiert.")

    @Slot(list)
    def _start_batch_transcription_from_database(self, video_ids: list[str]) -> None:
        """Startet Batch-Transcription für Videos aus dem Database Widget."""
        logger.info(f"Batch-Transcription für {len(video_ids)} Videos aus Database Widget angefordert.")

        if not video_ids:
            logger.warning("Keine Video-IDs für Batch-Transcription erhalten.")
            return

        # Hole den ProjectManagerService
        pm_service = self.service_factory.get_project_manager_service()

        # Erstelle TranscriptData-Objekte für alle Videos
        transcript_data_list = []
        for video_id in video_ids:
            transcript_data = pm_service.create_transcript_data_for_single(video_id)
            if not transcript_data.error_reason:
                transcript_data_list.append(transcript_data)
            else:
                logger.warning(
                    f"Konnte TranscriptData für Video {video_id} nicht erstellen: {transcript_data.error_reason}"
                )

        if not transcript_data_list:
            logger.error("Keine gültigen TranscriptData-Objekte für Batch-Transcription erstellt.")
            return

        logger.info(f"Starte Batch-Transcription für {len(transcript_data_list)} Videos")
        self.main_window.dashboard_widget.set_progress("Batch-Transcription läuft...", -1)

        self.worker_manager.start_worker(
            task_name="batch_transcription_from_database",
            worker_factory=lambda: BatchTranscriptionWorker(
                transcript_data_list=transcript_data_list,
                batch_transcription_service=self.service_factory.get_batch_transcription_service(),
            ),
            on_finish=self._on_batch_transcription_finished,
            on_error=self._on_worker_error,
        )

    @Slot(str)
    def _start_chapter_generation_worker(self, path_or_id: str) -> None:
        """Starts the ChapterGenerationWorker with dynamic prompt selection."""
        logger.info(f"[SignalHandler] _start_chapter_generation_worker called with: {path_or_id}")
        pm_service = self.service_factory.get_project_manager_service()
        file_service = self.service_factory.get_file_service()
        analysis_prompt_service = self.service_factory.get_analysis_prompt_service()

        # Pfad/ID-Ermittlung
        if os.path.isfile(path_or_id) and path_or_id.endswith("_transcript.md"):
            transcript_path = path_or_id
            video_id = os.path.basename(os.path.dirname(path_or_id))
        else:
            video_id = path_or_id
            transcript_path = pm_service.get_transcript_path_for_video_id(video_id)

        if not transcript_path or not video_id or not os.path.exists(transcript_path):
            logger.warning(f"Invalid path/transcript ID: transcript_path={transcript_path}, video_id={video_id}")
            return

        # Dynamische Prompt-Auswahl: Hole aktuellen Prompt-Typ aus VideoSelectionTable
        try:
            current_prompt_type = (
                self.main_window.batch_transcription_widget.video_selection_table.get_selected_prompt_type()
            )
            prompt_text = analysis_prompt_service.get_prompt(current_prompt_type)
            prompt_type_value = current_prompt_type.value
            logger.info(f"Using prompt type: {prompt_type_value}")
        except Exception as e:
            # Fallback auf Standard-Prompt
            logger.warning(f"Fehler beim Ermitteln des Prompt-Typs: {e}, verwende Fallback")
            from yt_database.services.analysis_prompt_service import PromptType

            current_prompt_type = PromptType.DETAILED_DATABASE
            prompt_text = analysis_prompt_service.get_prompt(current_prompt_type)
            prompt_type_value = current_prompt_type.value

        logger.info(f"Starting chapter generation for transcript: {video_id} with prompt type: {prompt_type_value}")
        self.main_window.dashboard_widget.set_progress("Generating chapters...", -1)

        worker = self.worker_manager.start_worker(
            task_name=f"chapter_generation_{video_id}",
            worker_factory=lambda: ChapterGenerationWorker(
                video_id=video_id,
                file_path=transcript_path,
                file_service=file_service,
                pm_service=pm_service,
                analysis_prompt_service=analysis_prompt_service,
                prompt_text=prompt_text,
                prompt_type=prompt_type_value,  # Explizit den Prompt-Typ übergeben
            ),
            on_finish=self._on_worker_finished,
            on_error=self._on_worker_error,
        )
        if worker:
            self.current_chapter_generation_worker = worker

        if worker and isinstance(self.main_window.web_window, WebEngineWindow):
            worker.send_transcript.connect(self.main_window.web_window.handle_new_transcript)
            self.main_window.web_window.chapters_extracted_signal.connect(worker.on_chapters_extracted)
            self.main_window.web_window.automation_sequence_failed.connect(worker.on_automation_failed)

            # Verbinde das neue Signal für Prompt-Updates
            worker.prompt_updated.connect(self.main_window.web_window.update_analysis_prompt)

            # Dynamische Prompt-Änderung während der Laufzeit
            self.main_window.batch_transcription_widget.video_selection_table.prompt_text_changed.connect(
                worker.on_prompt_type_changed
            )

    @Slot()
    def _on_worker_finished(self) -> None:
        """Universal callback on successful worker completion."""
        logger.info("Worker finished successfully.")
        self.main_window.dashboard_widget.clear_progress()

        # UI-Update für alle Widgets
        self.main_window.ui_update_requested.emit()

        # Spezifische Updates
        self.main_window.dashboard_widget._refresh_stats()

        # Database Widget explizit aktualisieren (falls ui_update_requested nicht ausreicht)
        if hasattr(self.main_window, "database_widget"):
            self.main_window.database_widget.reload_videos_in_table()

    @Slot(str)
    def _on_worker_error(self, error_msg: str) -> None:
        """Universal callback on worker error."""
        logger.error(f"Worker error: {error_msg}")
        self.main_window.dashboard_widget.clear_progress()

    @Slot(str)
    def _on_database_file_open_requested(self, video_id: str):
        """Callback for file open request - opens transcript in editor."""
        logger.info(f"File open requested for transcript: {video_id}")
        try:
            pm_service = self.service_factory.get_project_manager_service()
            file_path = pm_service.get_transcript_path_for_video_id(video_id)
            if file_path and hasattr(self.main_window, "show_file_in_text_editor"):
                self.main_window.show_file_in_text_editor(file_path)
                logger.info(f"File opened: {file_path}")
            else:
                logger.warning(f"Transcript file not found for transcript ID: {video_id}")
        except Exception as e:
            logger.error(f"Error opening file: {e}")

    @Slot(str)
    def _show_file_in_text_editor(self, file_path: str):
        """Callback for file display in editor - shows file."""
        logger.info(f"Opening file in editor: {file_path}")
        try:
            if os.path.exists(file_path):
                logger.info(f"File exists and would be opened: {file_path}")
                # Es ist ein Widget im stack des MainWindow, das den Texteditor darstellt

                self.main_window.text_file_editor_widget.load_file(file_path)
                self.main_window.stack.setCurrentWidget(self.main_window.text_file_editor_widget)

            else:
                logger.warning(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error opening file: {e}")

    @Slot()
    def _on_folder_selected(self):
        """Callback for folder selection."""
        logger.info("Folder selected.")

    @Slot(str, str)
    def _on_prompt_type_changed(self, prompt_type: str, description: str) -> None:
        """Called when the prompt type is changed in the VideoSelectionTable."""
        logger.info(f"Prompt type changed: {prompt_type}")
        self.main_window.statusBar().showMessage(f"Analysis prompt changed: {description}", 5000)

    @Slot()
    def _on_quick_batch_transcription(self):
        """Quick access: Navigates to the batch transcription widget."""
        logger.info("Dashboard: Quick batch transcription requested.")
        self.main_window.stack.setCurrentIndex(2)  # BatchTranscriptionWidget ist an Index 2

    @Slot()
    def _on_quick_database_refresh(self):
        """Quick access: Refreshes the database and UI."""
        logger.info("Dashboard: Database refresh requested.")
        self.main_window.dashboard_widget.set_progress("Updating database...", -1)
        try:
            self.main_window._on_ui_update_requested()
            self.main_window.dashboard_widget.clear_progress()
            logger.info("Database updated successfully.")
        except Exception as e:
            logger.error(f"Error during database refresh: {e}")
            self.main_window.dashboard_widget.clear_progress()

    @Slot()
    def _on_quick_settings(self):
        """Quick access: Opens settings."""
        logger.info("Dashboard: Settings requested.")
        self.main_window.config_dialog.show()

    @Slot()
    def _on_channel_analysis(self):
        """Quick access: Starts a channel analysis."""
        logger.info("Dashboard: Channel analysis requested.")
        self.main_window.stack.setCurrentIndex(1)  # Database Widget für Analyse
        logger.info("Channel analysis: Switching to database view for analysis features.")

    @Slot(str)
    def _perform_search(self, keyword: str):
        """Performs a search using the ProjectManagerService."""
        try:
            logger.info(f"SearchWidget: Performing search for keyword: {keyword}")
            project_manager = self.service_factory.get_project_manager_service()
            results = project_manager.search_chapters(keyword)

            logger.info(f"SearchWidget: Found {len(results)} results for '{keyword}'")
            self.main_window.search_widget.display_results(results)

        except Exception as e:
            logger.error(f"SearchWidget: Error during search: {e}")
            self.main_window.search_widget.display_results([])

    # Private Callback-Methoden - vereinfacht
    def _on_channel_videos_finished(self) -> None:
        """Callback bei erfolgreichem Abschluss des Channel-Transcript-Workers."""
        logger.info("Channel-Transcripts erfolgreich geladen.")
        self.main_window.progress_cleared.emit()
        self.main_window.ui_update_requested.emit()

    def _on_channel_videos_error(self, error_msg: str) -> None:
        """Callback bei Fehler im Channel-Transcript-Worker."""
        logger.error(f"Fehler beim Laden der Channel-Transcripts: {error_msg}")
        self.main_window.progress_cleared.emit()

    def _on_batch_transcription_finished(self) -> None:
        """Callback bei erfolgreichem Abschluss der Batch-Transkription."""
        logger.info("Batch-Transkription erfolgreich abgeschlossen.")
        self.main_window.dashboard_widget.clear_progress()

        # UI-Update für alle Widgets
        self.main_window.ui_update_requested.emit()

        # Spezifische Updates nach Batch-Transcription
        self.main_window.dashboard_widget._refresh_stats()
        if hasattr(self.main_window, "database_widget"):
            self.main_window.database_widget.reload_videos_in_table()
            logger.info("Database Widget nach Batch-Transcription aktualisiert.")

    def _on_batch_transcription_error(self, error_msg: str) -> None:
        """Callback bei Fehler in der Batch-Transkription."""
        logger.error(f"Fehler bei Batch-Transkription: {error_msg}")
        self.main_window.progress_cleared.emit()

    def _on_chapter_generation_finished(self) -> None:
        """Callback bei erfolgreichem Abschluss der Kapitelgenerierung."""
        logger.info("Kapitelgenerierung erfolgreich abgeschlossen.")
        self.main_window.progress_cleared.emit()
        self.main_window.ui_update_requested.emit()

    def _on_chapter_generation_error(self, error_msg: str) -> None:
        """Callback bei Fehler in der Kapitelgenerierung."""
        logger.error(f"Fehler bei Kapitelgenerierung: {error_msg}")
        self.main_window.progress_cleared.emit()

    def on_prompt_text_changed(self, prompt_text: str, description: str) -> None:
        """Leitet den neuen Prompt-Text an den laufenden ChapterGenerationWorker weiter.

        Args:
            prompt_text (str): Der neue Prompt-Text.
            description (str): Beschreibung des Prompts.
        """
        worker = getattr(self, "current_chapter_generation_worker", None)
        if worker is not None:
            logger.debug(f"Leite neuen Prompt-Text an Worker weiter: {prompt_text}")
            worker.on_prompt_text_changed(prompt_text)

    @Slot(str)
    def _show_transcript_in_text_editor(self, video_id: str):
        """Shows transcript file for given video_id in the integrated text editor."""
        logger.info(f"Opening transcript in text editor for video_id: {video_id}")
        try:
            # Import hier um zirkuläre Imports zu vermeiden
            from peewee import DoesNotExist

            from yt_database.config.settings import settings
            from yt_database.database import Transcript
            from yt_database.utils.transcript_for_video_id_util import get_transcript_path_for_video_id

            # Hole Channel-ID für das Video
            try:
                transcript = Transcript.get(Transcript.video_id == video_id)
                channel_id = transcript.channel.channel_id
            except DoesNotExist:
                logger.error(f"Transcript not found for video_id: {video_id}")
                return

            # Bestimme Pfad zur Transkript-Datei
            transcript_path = get_transcript_path_for_video_id(settings.project_path, channel_id, video_id)

            if transcript_path and os.path.exists(transcript_path):
                logger.info(f"Loading transcript file: {transcript_path}")
                self.main_window.text_file_editor_widget.load_file(transcript_path)
                self.main_window.stack.setCurrentWidget(self.main_window.text_file_editor_widget)
            else:
                logger.warning(f"Transcript file not found for video_id: {video_id}")

        except Exception as e:
            logger.error(f"Error opening transcript in text editor: {e}")

    def _on_settings_toolbar_clicked(self) -> None:
        """Handle settings toolbar action click."""
        self.main_window.config_dialog.show()
        self.main_window.config_dialog.raise_()
        self.main_window.config_dialog.activateWindow()

    def _on_settings_saved(self, config: dict) -> None:
        """Handle when settings are saved in config dialog.

        Args:
            config: The updated configuration dictionary
        """
        logger.info(f"Settings received from dialog: {config}")
        try:
            for key, value in config.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
                    logger.debug(f"Set setting '{key}' to '{value}'")
                else:
                    logger.warning(f"Attempted to set unknown setting '{key}'")

            settings.save_to_yaml()
            logger.info("Configuration successfully saved to yt_database.yaml")
            self.main_window.statusBar().showMessage("Settings saved successfully.", 5000)

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            self.main_window.statusBar().showMessage("Error saving settings.", 5000)

    def _on_config_dialog_cancelled(self) -> None:
        """Handle when config dialog is cancelled."""
        logger.debug("Config dialog cancelled")

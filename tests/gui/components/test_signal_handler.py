"""
Test für SignalHandler

Testet die Instanziierung des SignalHandler mit Dummy-Abhängigkeiten.
"""

import pytest
from PySide6.QtCore import QObject
from src.yt_database.gui.components.signal_handler import SignalHandler

class DummyMainWindow(QObject):
    def __init__(self):
        super().__init__()
        self.notebook_action = DummySignal()
        self.sidebar = DummySidebar()
        self.dashboard_widget = DummyDashboardWidget()
        self.batch_transcription_widget = DummyBatchTranscriptionWidget()
        self.database_widget = DummyDatabaseWidget()
        self.search_widget = DummySearchWidget()
        self.config_dialog = DummyConfigDialog()
        self.settings_toolbar_action = DummySignal()
        self.explorer_widget = DummyExplorerWidget()
        self.log_message_received = DummySignal()
        self.log_widget = DummyLogWidget()
        self.stack = DummyStack()

class DummySignal(QObject):
    def connect(self, slot):
        pass

class DummySidebar(QObject):
    dashboard_requested = DummySignal()
    database_requested = DummySignal()
    transcripts_requested = DummySignal()
    search_requested = DummySignal()
    log_requested = DummySignal()
    text_editor_requested = DummySignal()

class DummyDashboardWidget(QObject):
    quick_batch_transcription_requested = DummySignal()
    quick_database_refresh_requested = DummySignal()
    quick_settings_requested = DummySignal()
    channel_analysis_requested = DummySignal()
    set_progress = lambda *a, **kw: None

class DummyBatchTranscriptionWidget(QObject):
    channel_videos_requested = DummySignal()
    batch_transcription_requested = DummySignal()
    file_open_requested = DummySignal()
    chapter_generation_requested = DummySignal()
    text_editor_open_requested = DummySignal()
    video_selection_table = type('Dummy', (), {'prompt_text_changed': DummySignal()})()
    force_metadata = False

class DummyDatabaseWidget(QObject):
    chapter_generation_requested = DummySignal()
    file_open_requested = DummySignal()
    text_editor_open_requested = DummySignal()
    single_transcription_requested = DummySignal()
    batch_transcription_requested = DummySignal()

class DummySearchWidget(QObject):
    search_requested = DummySignal()

class DummyConfigDialog(QObject):
    settingsSaved = DummySignal()
    dialogCancelled = DummySignal()

class DummyExplorerWidget(QObject):
    file_selected = DummySignal()
    folder_selected = DummySignal()
    chapter_generation_requested = DummySignal()

class DummyLogWidget(QObject):
    receive_log = lambda *a, **kw: None

class DummyStack(QObject):
    def setCurrentIndex(self, idx):
        pass

class DummyServiceFactory:
    pass

class DummyWorkerManager:
    pass

def test_signal_handler_instantiation():
    main_window = DummyMainWindow()
    service_factory = DummyServiceFactory()
    worker_manager = DummyWorkerManager()
    handler = SignalHandler(main_window, service_factory, worker_manager)
    assert handler.main_window is main_window
    assert handler.service_factory is service_factory
    assert handler.worker_manager is worker_manager

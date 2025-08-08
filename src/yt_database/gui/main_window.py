# src/yt_database/gui/main_window.py

import os
import sys
from typing import Optional

from loguru import logger
from PySide6.QtCore import Signal, Slot, qInstallMessageHandler
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QToolBar

from yt_database.config import logging_config  # noqa: F401
from yt_database.config.settings import settings

from yt_database.gui.components.font_manager import FontManager
from yt_database.gui.components.signal_handler import SignalHandler
from yt_database.gui.components.ui_manager import UiManager
from yt_database.gui.widgets.batch_transcription_control_widget import BatchTranscriptionWidget

from yt_database.gui.widgets.config_dialog import ConfigDialog
from yt_database.gui.widgets.dashboard_widget import DashboardWidget
from yt_database.gui.widgets.database_table_view_widget import DatabaseOverviewWidget
from yt_database.gui.widgets.log_widget import LogWidget
from yt_database.gui.widgets.projects_tree_view_widget import ProjectTreeWidget
from yt_database.gui.widgets.search_widget_table import SearchWidget
from yt_database.gui.widgets.sidebar_widget import SidebarWidget
from yt_database.gui.widgets.text_file_editor_widget import TextFileEditorWidget
from yt_database.gui.components.worker_manager import WorkerManager
from yt_database.services.factory_config import create_service_factory
from yt_database.services.protocols import WebEngineWindowProtocol
from yt_database.services.service_factory import ServiceFactory


if settings.debug:
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    logger.add(
        sink="logs/yt_database.log",
        level="DEBUG",
        rotation="1 day",
        retention="7 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        filter=lambda record: record["level"].name in ("DEBUG", "WARNING", "ERROR", "CRITICAL", "INFO"),
    )


class MainWindow(QMainWindow):
    """Hauptfenster mit Seitenleiste und zentralem Widget-Stack."""

    log_message_received: Signal = Signal(str, str)
    ui_update_requested = Signal()
    progress_cleared = Signal()

    def __init__(self, app: QApplication, service_factory: Optional[ServiceFactory] = None) -> None:
        super().__init__()
        self.app = app  # Speichern der App-Instanz
        self.setWindowTitle("YT Database Mission Control")
        self.web_window: Optional[WebEngineWindowProtocol] = None
        self.sidebar: SidebarWidget
        self.stack: QStackedWidget
        self.dashboard_widget: DashboardWidget
        self.explorer_widget: ProjectTreeWidget
        self.database_widget: DatabaseOverviewWidget
        self.batch_transcription_widget: BatchTranscriptionWidget
        self.text_file_editor_widget: TextFileEditorWidget
        self.search_widget: SearchWidget
        self.notebook_action: QAction
        self.settings_toolbar_action: QAction
        self.log_widget: LogWidget
        self.toolbar: QToolBar
        self.config_dialog: ConfigDialog

        self.font_manager = FontManager()
        self.font_manager.setup_inter_font()

        self._setup_worker_manager()
        self._setup_service_factory(service_factory)
        self._setup_ui_manager()
        self._setup_signal_handler()

        x, y, w, h = map(int, settings.main_window_geometry.split(","))
        self.setGeometry(x, y, w, h)

        self._setup_logging_sink()
        logger.info("MainWindow: Initialisierung abgeschlossen.")

    def _setup_logging_sink(self) -> None:
        """Konfiguriert einen Loguru-Sink, der Nachrichten an die GUI weiterleitet."""
        logger.info("Setze GUI-Logging-Sink auf.")

        def gui_sink(message):
            record = message.record
            log_line = (
                f"{record['time'].strftime('%Y-%m-%d %H:%M:%S')}|"
                f"{record['level'].name}|{record['name']}:{record['function']}:{record['line']}|{record['message']}"
            )
            self.log_message_received.emit(record["level"].name, log_line)

        log_level = "DEBUG" if getattr(settings, "debug", False) else "INFO"
        logger.add(gui_sink, level=log_level, enqueue=True, catch=False)

    def _setup_worker_manager(self) -> None:
        """Initialisiert den Worker Manager für async Operations."""
        self.worker_manager = WorkerManager(main_window=self)

    def _setup_service_factory(self, service_factory: Optional[ServiceFactory]) -> None:
        """Setup oder Übernahme der Service Factory."""
        if service_factory is not None:
            logger.debug("ServiceFactory übergeben.")
            self.service_factory = service_factory
        else:
            logger.debug("Erzeuge eigene ServiceFactory.")
            self.service_factory = create_service_factory()

    def _setup_ui_manager(self) -> None:
        """Initialisiert den UiManager, der für die Erstellung und Anordnung der UI-Komponenten verantwortlich ist."""
        self.ui_manager = UiManager(self, self.service_factory, self.font_manager)
        self.ui_manager.setup_ui()

    def _setup_signal_handler(self) -> None:
        """Initialisiert den SignalHandler, der die Anwendungslogik kapselt."""
        self.signal_handler = SignalHandler(
            self, worker_manager=self.worker_manager, service_factory=self.service_factory
        )
        self.signal_handler.connect_signals()

    @Slot(str)
    def _log_message(self, level: str, message: str) -> None:
        """Slot zum Empfangen von Log-Nachrichten und Weiterleiten an Loguru."""
        logger.log(level, message)

    @Slot()
    def _on_ui_update_requested(self) -> None:
        """Slot, der auf das ui_update_requested Signal reagiert."""
        logger.info("UI-Update angefordert. Führe notwendige Aktualisierungen durch.")
        self.database_widget.refresh_data()
        self.dashboard_widget._refresh_stats()

    @Slot()
    def show_notebook_lm_window(self) -> None:
        """Öffnet das WebEngineWindow für die NotebookLM-Automatisierung."""
        logger.debug("Zeige NotebookLM-Fenster.")
        if self.web_window is None:
            self.web_window = self.service_factory.get_web_engine_window(parent=self)
            if hasattr(self.web_window, "set_url"):
                self.web_window.set_url(settings.webview_url)
        if self.web_window is not None:
            if hasattr(self.web_window, "isVisible") and not self.web_window.isVisible():
                if hasattr(self.web_window, "show"):
                    self.web_window.show()
            if hasattr(self.web_window, "activateWindow"):
                self.web_window.activateWindow()
            if hasattr(self.web_window, "raise_"):
                self.web_window.raise_()

    def show_file_in_text_editor(self, file_path: str) -> None:
        """Öffnet die angegebene Datei im integrierten Text-Editor."""
        from loguru import logger

        if os.path.exists(file_path):
            logger.info(f"Datei wird im Editor geöffnet: {file_path}")
            try:
                # Lade die Datei in den Text-Editor
                self.text_file_editor_widget.load_file(file_path)

                # Wechsle zum Text-Editor-Widget (Index 5 im Stacked Widget)
                if hasattr(self, "stack"):
                    self.stack.setCurrentIndex(5)
                    logger.debug("Wechsel zum Text-Editor-Widget erfolgreich")
                else:
                    logger.warning("Stacked Widget nicht gefunden - kann nicht zum Text-Editor wechseln")

            except Exception as e:
                logger.error(f"Fehler beim Öffnen der Datei im Text-Editor: {e}")
        else:
            logger.warning(f"Datei nicht gefunden: {file_path}")

    def closeEvent(self, event) -> None:
        """Beendet alle laufenden Worker und schließt das WebEngineWindow vor dem Schließen."""
        # Beende alle laufenden Worker sanft
        if hasattr(self, "worker_manager") and hasattr(self.worker_manager, "running_tasks"):
            for task in list(self.worker_manager.running_tasks.values()):
                worker = task.get("worker")
                if worker and hasattr(worker, "stop_worker"):
                    try:
                        logger.info(f"Beende Worker: {worker}")
                        worker.stop_worker()
                    except Exception as e:
                        logger.warning(f"Fehler beim Beenden des Workers: {e}")
        # Schließe das WebEngineWindow, falls offen
        if self.web_window is not None and hasattr(self.web_window, "isVisible") and self.web_window.isVisible():
            logger.info("Schließe das WebEngineWindow.")
            getattr(self.web_window, "close", lambda: None)()
        super().closeEvent(event)


# Funktion zum Filtern von Qt-Nachrichten
def qt_message_handler(mode, context, message):
    """
    Ein benutzerdefinierter Handler, der die Font-Rendering-Fehler unterdrückt.
    """
    if "render glyph failed" in message or "QFontEngine" in message:
        return  # Diese spezifische Nachricht einfach ignorieren und nichts tun.

    # Hier könnte man optional andere Qt-Nachrichten an die Konsole weiterleiten,
    # aber für eine saubere Ausgabe lasse ich das weg.
    # print(f"QT-MSG: {message}")


def main() -> None:
    """Einstiegspunkt für das GUI-Programm."""
    import sys

    from PySide6.QtWidgets import QApplication

    qInstallMessageHandler(qt_message_handler)
    app = QApplication(sys.argv)
    window = MainWindow(app=app)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

# src/yt_database/gui/components/ui_manager.py

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QWidget,
)

from yt_database.config.settings import settings

# <<< NEU >>> Importieren des StyleManagers
from yt_database.gui.components.style_manager import StyleManager
from yt_database.gui.utils.icons import Icons
from yt_database.gui.widgets.batch_transcription_control_widget import (
    BatchTranscriptionWidget as BatchTranscriptionWidget,
)
from yt_database.gui.widgets.config_dialog import ConfigDialog
from yt_database.gui.widgets.dashboard_widget import DashboardWidget
from yt_database.gui.widgets.database_table_view_widget import DatabaseOverviewWidget
from yt_database.gui.widgets.log_widget import LogWidget
from yt_database.gui.widgets.projects_tree_view_widget import ProjectTreeWidget
from yt_database.gui.widgets.search_widget_table import SearchWidget
from yt_database.gui.widgets.sidebar_widget import SidebarWidget
from yt_database.gui.widgets.text_file_editor_widget import TextFileEditorWidget

# Import der Ressourcen-Datei - muss vor erstem Icon-Zugriff importiert werden
from yt_database.resources import icons_rc  # noqa: F401

if TYPE_CHECKING:
    from yt_database.gui.components.font_manager import FontManager
    from yt_database.gui.main_window import MainWindow
    from yt_database.services.service_factory import ServiceFactory


class UiManager:
    """Verwaltet die Erstellung, das Layout und die Einrichtung aller UI-Widgets für das Hauptfenster."""

    def __init__(self, main_window: MainWindow, service_factory: ServiceFactory, font_manager: FontManager):
        self.main_window = main_window
        self.service_factory = service_factory
        self.font_manager = font_manager
        self.style_manager: StyleManager | None = None

    def setup_ui(self) -> None:
        """Initialisiert die gesamte Benutzeroberfläche."""
        self._setup_style_manager()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_widgets()
        self._setup_layout()
        self._apply_fonts_to_widgets()

    def _setup_widgets(self) -> None:
        """Initialisiert alle Widgets für das Hauptfenster."""
        logger.debug("UiManager: Initialisiert die Widgets.")
        projects_dir = settings.project_path

        self.main_window.sidebar = SidebarWidget()
        self.main_window.stack = QStackedWidget()
        self.main_window.dashboard_widget = DashboardWidget(service_factory=self.service_factory)
        self.main_window.text_file_editor_widget = TextFileEditorWidget(
            title="Text File Editor",
            content="",
            file_path="",
            parent=self.main_window,
        )

        self.main_window.explorer_widget = ProjectTreeWidget(projects_dir)

        self.main_window.database_widget = DatabaseOverviewWidget(
            self.service_factory.get_project_manager_service(), self.main_window
        )

        self.main_window.batch_transcription_widget = BatchTranscriptionWidget(
            pm_service=self.service_factory.get_project_manager_service(),
            yt_service=self.service_factory.get_transcript_service(),
            on_error=lambda msg: logger.warning(msg),
        )

        self.main_window.search_widget = SearchWidget()

        self.main_window.log_widget = LogWidget()

        # Config Dialog (wird nur bei Bedarf angezeigt)
        self.main_window.config_dialog = ConfigDialog(parent=self.main_window)

    def _apply_fonts_to_widgets(self) -> None:
        """Applies the Inter font to all relevant widgets."""
        if self.font_manager.is_inter_loaded():
            widgets_dict = {
                "sidebar": self.main_window.sidebar,
                "dashboard_widget": self.main_window.dashboard_widget,
                "explorer_widget": self.main_window.explorer_widget,
                "database_widget": self.main_window.database_widget,
                "batch_transcription_widget": self.main_window.batch_transcription_widget,
                "log_widget": self.main_window.log_widget,
            }
            self.font_manager.apply_fonts_to_widgets(widgets_dict)

    def _setup_layout(self) -> None:
        """
        Initialisiert das Hauptlayout der Anwendung.
        """
        logger.debug("UiManager: Initialisiert das Layout.")
        stack = self.main_window.stack
        stack.addWidget(self.main_window.dashboard_widget)
        stack.addWidget(self.main_window.database_widget)
        stack.addWidget(self.main_window.batch_transcription_widget)
        stack.addWidget(self.main_window.search_widget)
        stack.addWidget(self.main_window.log_widget)
        stack.addWidget(self.main_window.text_file_editor_widget)

        main_panel = QWidget()
        main_layout = QHBoxLayout(main_panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_window.sidebar)
        main_layout.addWidget(stack)

        splitter = QSplitter()
        splitter.addWidget(self.main_window.explorer_widget)
        splitter.addWidget(main_panel)

        # Verbessere die Größenverteilung
        splitter.setStretchFactor(0, 1)  # Explorer bekommt Platz zum Wachsen
        splitter.setStretchFactor(1, 3)  # Main Panel bekommt 3x mehr Platz

        # Setze explizite Anfangsgrößen
        splitter.setSizes([300, 900])  # Explorer: 300px, Main Panel: 900px
        splitter.setHandleWidth(5)  # Sichtbarer Griff
        # Lasse Kollaps zu, damit der Benutzer den Explorer ausblenden kann

        self.main_window.setCentralWidget(splitter)

    def _setup_toolbar(self) -> None:
        """Initialisiert die Toolbar."""
        logger.debug("UiManager: Initialisiert die Toolbar.")
        self.main_window.toolbar = QToolBar("Hauptwerkzeugleiste")
        self.main_window.addToolBar(self.main_window.toolbar)

        # Icons aus QRC-Ressourcen über Icons-Klasse laden
        self.main_window.notebook_action = QAction(Icons.get(Icons.NOTEBOOK), "NotebookLM öffnen", self.main_window)
        self.main_window.settings_toolbar_action = QAction(Icons.get(Icons.SETTINGS), "Einstellungen", self.main_window)

        self.main_window.toolbar.addAction(self.main_window.notebook_action)
        self.main_window.toolbar.addSeparator()
        self.main_window.toolbar.addAction(self.main_window.settings_toolbar_action)

    def _setup_statusbar(self) -> None:
        """Initialisiert die Statusbar."""
        logger.debug("UiManager: Initialisiert die Statusbar.")
        self.main_window.statusBar().showMessage("Bereit.")

    # <<< NEU >>> Diese Methode erstellt und aktiviert den StyleManager
    def _setup_style_manager(self) -> None:
        """Initialisiert den StyleManager für das initiale Laden und das Live-Stylesheet-Reloading."""
        logger.debug("UiManager: Initialisiert den StyleManager.")
        # Ich erstelle eine Instanz des StyleManagers.
        # WICHTIG: Wir speichern eine Referenz in self.style_manager, damit das Objekt nicht
        # sofort vom Garbage Collector entfernt wird.
        # Das MainWindow wird als Parent gesetzt, was für eine saubere Qt-Objekthierarchie sorgt.
        self.style_manager = StyleManager(app=self.main_window.app, parent=self.main_window)

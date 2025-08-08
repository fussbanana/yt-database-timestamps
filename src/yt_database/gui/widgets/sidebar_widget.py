"""
SidebarWidget für die Hauptnavigation.
PEP8, Google-Style Docstring, Typisierung.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget

from yt_database.gui.utils.icons import Icons


class SidebarWidget(QWidget):
    """Seitenleiste für die Hauptnavigation."""

    dashboard_requested = Signal()
    database_requested = Signal()
    transcripts_requested = Signal()
    search_requested = Signal()
    log_requested = Signal()
    text_editor_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        """Initialisiert die UI-Struktur."""
        self._setup_widgets()
        self._setup_layout()
        self._setup_signals()

    def _setup_widgets(self) -> None:
        """Erstellt die Buttons für die Navigation."""
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_dashboard.setObjectName("sidebar_btn_dashboard")
        self.btn_dashboard.setIcon(Icons.get(":/icons/dashboard-3.svg"))
        self.btn_database = QPushButton("Datenbank")
        self.btn_database.setObjectName("sidebar_btn_database")
        self.btn_database.setIcon(Icons.get(":/icons/database.svg"))
        self.btn_transcripts = QPushButton("Transkripte")
        self.btn_transcripts.setObjectName("sidebar_btn_transcripts")
        self.btn_transcripts.setIcon(Icons.get(":/icons/markdown-document-programming.svg"))
        self.btn_search = QPushButton("Suche")
        self.btn_search.setObjectName("sidebar_btn_search")
        self.btn_search.setIcon(Icons.get(":/icons/search-visual.svg"))
        self.btn_log = QPushButton("Log")
        self.btn_log.setObjectName("sidebar_btn_log")
        self.btn_log.setIcon(Icons.get(":/icons/bug-virus-document.svg"))
        self.btn_text_editor = QPushButton("Text Editor")
        self.btn_text_editor.setObjectName("sidebar_btn_text_editor")
        self.btn_text_editor.setIcon(Icons.get(":/icons/text-style.svg"))
        self.btn_close_worker = QPushButton("Arbeiter beenden")
        self.btn_close_worker.setObjectName("sidebar_btn_close_worker")
        self.btn_close_worker.setIcon(Icons.get(":/icons/emergency-exit.svg"))
        # ... weitere Buttons
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

    def _setup_layout(self) -> None:
        """Fügt die Buttons ins Layout ein."""
        layout = QVBoxLayout(self)
        layout.addWidget(self.btn_dashboard)
        layout.addWidget(self.btn_database)
        layout.addWidget(self.btn_transcripts)
        layout.addWidget(self.btn_search)
        layout.addWidget(self.btn_log)
        layout.addWidget(self.btn_text_editor)
        layout.addWidget(self.btn_close_worker)
        layout.addItem(self.verticalSpacer)
        layout.addStretch()

    def _setup_signals(self) -> None:
        """Verbindet die Buttons mit den Signalen."""
        self.btn_dashboard.clicked.connect(self.dashboard_requested.emit)
        self.btn_database.clicked.connect(self.database_requested.emit)
        self.btn_transcripts.clicked.connect(self.transcripts_requested.emit)
        self.btn_search.clicked.connect(self.search_requested.emit)
        self.btn_log.clicked.connect(self.log_requested.emit)
        self.btn_text_editor.clicked.connect(self.text_editor_requested.emit)

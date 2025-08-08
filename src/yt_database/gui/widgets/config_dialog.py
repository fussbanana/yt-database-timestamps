"""
Dieses Modul definiert den Konfigurationsdialog für die yt-database Anwendung.

Der `ConfigDialog` bietet eine grafische Benutzeroberfläche (GUI), um zentrale
Anwendungseinstellungen zu bearbeiten. Anstatt die Einstellungen direkt zu speichern,
verwendet dieser Dialog ein Signal-Slot-basiertes Design, um die Änderungen an einen
externen Handler zu übergeben.
"""

import os

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from yt_database.config.settings import settings


class ConfigDialog(QDialog):
    """Ein Dialog zur Konfiguration der Anwendungseinstellungen via Signalen."""

    settingsSaved = Signal(dict)
    dialogCancelled = Signal()

    def __init__(self, parent=None):
        """Initialisiert den ConfigDialog."""
        logger.debug("Initializing ConfigDialog...")
        super().__init__(parent)

        self._setup_ui()
        self.load_settings()
        logger.debug("ConfigDialog initialized successfully.")

    def _setup_ui(self) -> None:
        """Ruft die UI-Setup-Methoden in der richtigen Reihenfolge auf."""
        logger.debug("Setting up UI for ConfigDialog...")
        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()
        logger.debug("UI setup for ConfigDialog complete.")

    def _setup_widgets(self) -> None:
        """Initialisiert alle UI-Komponenten und konfiguriert ihre statischen Eigenschaften."""
        logger.debug("Creating widgets for ConfigDialog...")
        self.setWindowTitle("Einstellungen")
        self.setMinimumWidth(500)

        # Eingabefeld für den Projektpfad.
        self.project_path_input = QLineEdit()
        self.project_path_input.setObjectName("project_path_input")
        self.project_path_input.setPlaceholderText("Pfad zum Projektordner")
        self.project_path_input.setToolTip(
            "Pfad zum Hauptordner, in dem alle Projekte gespeichert werden. Beispiel: ./projects"
        )
        self.project_path_button = QPushButton("Durchsuchen...")
        self.project_path_button.setObjectName("project_path_button")
        self.project_path_button.setToolTip("Öffnet einen Dialog zur Auswahl des Projektordners.")

        # Eingabefeld für den Cookie-Pfad.
        self.cookie_path_input = QLineEdit()
        self.cookie_path_input.setObjectName("cookie_path_input")
        self.cookie_path_input.setPlaceholderText("Pfad zur cookies.txt (optional)")
        self.cookie_path_input.setToolTip(
            "Pfad zur cookies.txt, die für yt-dlp verwendet wird. Notwendig für private oder regionale YouTube-Videos."
        )
        self.cookie_path_button = QPushButton("Durchsuchen...")
        self.cookie_path_button.setObjectName("cookie_path_button")
        self.cookie_path_button.setToolTip("Öffnet einen Dialog zur Auswahl der Cookie-Datei.")

        # Checkbox zur Aktivierung der Cookie-Nutzung.
        self.use_cookies_check = QCheckBox("Cookies für yt-dlp verwenden (empfohlen für private/regionale Videos)")
        self.use_cookies_check.setObjectName("use_cookies_check")
        self.use_cookies_check.setToolTip(
            "Aktiviert die Verwendung von Cookies für yt-dlp. Empfohlen für Videos, die einen Login oder spezielle Regionseinstellungen benötigen."
        )

        # Checkbox zur Aktivierung des Debug-Modus.
        self.debug_mode_check = QCheckBox("Debug-Modus aktivieren")
        self.debug_mode_check.setObjectName("debug_mode_check")
        self.debug_mode_check.setToolTip(
            "Zeigt zusätzliche Debug-Ausgaben im Log an. Nur für Fehlersuche und Entwicklung aktivieren."
        )

        # Eingabefeld für die WebView URL
        self.webview_url_input = QLineEdit()
        self.webview_url_input.setObjectName("webview_url_input")
        self.webview_url_input.setPlaceholderText("https://notebooklm.google.com/notebook/...")
        self.webview_url_input.setToolTip(
            "URL, die im WebView-Fenster angezeigt wird. Beispiel: NotebookLM-Notizbuch oder andere Webanwendung."
        )

        # SpinBox für das Standard-Abfrageintervall.
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setObjectName("interval_spinbox")
        self.interval_spinbox.setRange(1, 3600)
        self.interval_spinbox.setSuffix(" s")
        self.interval_spinbox.setToolTip(
            "Wie oft (in Sekunden) neue Daten automatisch abgefragt werden.\nUm IP-Sperren zu vermeiden, sollte das Intervall nicht zu kurz gewählt werden."
        )

        # SpinBox für die maximale Anzahl an Videos.
        self.max_videos_spinbox = QSpinBox()
        self.max_videos_spinbox.setObjectName("max_videos_spinbox")
        self.max_videos_spinbox.setRange(1, 1000)
        self.max_videos_spinbox.setSuffix(" Videos")
        self.max_videos_spinbox.setToolTip("Maximale Anzahl an Videos, die bei einer Abfrage verarbeitet werden.")

        # Standard-Buttons zum Speichern oder Abbrechen.
        self.save_button = QPushButton("Speichern")
        self.save_button.setObjectName("save_button")
        self.save_button.setToolTip("Speichert alle vorgenommenen Einstellungen und schließt den Dialog.")
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.setToolTip("Verwirft alle Änderungen und schließt den Dialog.")
        logger.debug("Widgets created and object names set.")

    def _setup_layouts(self) -> None:
        """Ordnet die initialisierten Widgets in Layouts an."""
        logger.debug("Arranging widgets in layouts...")
        main_layout = QVBoxLayout()

        form_layout = QFormLayout()

        project_path_layout = QHBoxLayout()
        project_path_layout.addWidget(self.project_path_input)
        project_path_layout.addWidget(self.project_path_button)
        form_layout.addRow("Projekt-Ordner:", project_path_layout)

        cookie_layout = QHBoxLayout()
        cookie_layout.addWidget(self.cookie_path_input)
        cookie_layout.addWidget(self.cookie_path_button)
        form_layout.addRow("Cookie-Datei (für yt-dlp):", cookie_layout)

        form_layout.addRow(self.use_cookies_check)
        form_layout.addRow(self.debug_mode_check)
        form_layout.addRow("WebView URL:", self.webview_url_input)
        form_layout.addRow("Standard-Intervall:", self.interval_spinbox)
        form_layout.addRow("Standard Max. Videos:", self.max_videos_spinbox)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        logger.debug("Layouts arranged.")

    def _setup_signals(self) -> None:
        """Verbindet die Signale der permanenten Widgets mit ihren Slots."""
        logger.debug("Connecting signals...")
        self.project_path_button.clicked.connect(self.select_project_dir)
        self.cookie_path_button.clicked.connect(self.select_cookie_file)
        self.save_button.clicked.connect(self._on_save_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        logger.debug("Signals connected.")

    def select_project_dir(self) -> None:
        """Öffnet einen Dialog zur Auswahl eines Verzeichnisses für den Projektpfad."""
        logger.debug("Opening directory dialog for project path...")
        path = QFileDialog.getExistingDirectory(self, "Projekt-Ordner auswählen", self.project_path_input.text())
        if path:
            logger.debug(f"Project path selected: {path}")
            self.project_path_input.setText(path)

    def select_cookie_file(self) -> None:
        """Öffnet einen Dialog zur Auswahl einer Cookie-Datei."""
        logger.debug("Opening file dialog for cookie file...")
        path, _ = QFileDialog.getOpenFileName(self, "Cookie-Datei auswählen", "", "Textdateien (*.txt)")
        if path:
            logger.debug(f"Cookie file selected: {path}")
            self.cookie_path_input.setText(path)

    def load_settings(self) -> None:
        """Lädt die aktuellen Einstellungen in die UI-Felder."""
        logger.debug("Loading settings into dialog...")
        self.project_path_input.setText(settings.project_path)
        self.cookie_path_input.setText(settings.yt_dlp_cookies_path)
        self.use_cookies_check.setChecked(getattr(settings, "use_yt_dlp_cookies", True))
        self.debug_mode_check.setChecked(settings.debug)
        self.webview_url_input.setText(settings.webview_url)
        self.interval_spinbox.setValue(settings.default_interval)
        self.max_videos_spinbox.setValue(settings.default_max_videos)
        logger.debug("Settings loaded.")

    def _on_save_clicked(self) -> None:
        """Validiert die Eingaben, sendet das `settingsSaved`-Signal und schließt den Dialog."""
        logger.debug("Save button clicked, validating inputs...")
        project_path = self.project_path_input.text()
        if not project_path or not os.path.isdir(project_path):
            logger.warning(f"Invalid project path provided: {project_path}")
            QMessageBox.warning(
                self,
                "Ungültiger Pfad",
                "Der angegebene Projekt-Ordner ist kein gültiges Verzeichnis.",
            )
            return

        cookie_path = self.cookie_path_input.text()
        if cookie_path and not os.path.exists(cookie_path):
            logger.warning(f"Invalid cookie path provided: {cookie_path}")
            QMessageBox.warning(self, "Ungültiger Pfad", "Die angegebene Cookie-Datei existiert nicht.")
            return

        config = {
            "project_path": project_path,
            "yt_dlp_cookies_path": cookie_path,
            "use_yt_dlp_cookies": self.use_cookies_check.isChecked(),
            "debug": self.debug_mode_check.isChecked(),
            "webview_url": self.webview_url_input.text(),
            "default_interval": self.interval_spinbox.value(),
            "default_max_videos": self.max_videos_spinbox.value(),
        }

        logger.debug(f"Validation successful. Emitting settingsSaved signal with config: {config}")
        self.settingsSaved.emit(config)
        self.accept()

    def _on_cancel_clicked(self) -> None:
        """Sendet das `dialogCancelled`-Signal und schließt den Dialog."""
        logger.debug("Cancel button clicked. Emitting dialogCancelled signal.")
        self.dialogCancelled.emit()
        self.reject()

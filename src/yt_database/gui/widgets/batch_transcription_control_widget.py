"""
BatchTranscriptionWidget
-----------------------
Widget für die Steuerung der Batch-Transkription (Kanal-URL, Intervall, Max Transcripts, Provider, Buttons, Progressbar, Checkbox).
Kapselt alle Controls und das Layout für den Batch-Transkriptions-Workflow.
Alle öffentlichen Attribute sind als Properties verfügbar.
Google-Style-Docstrings und Typ-Hints werden verwendet.
"""

from typing import Callable, List, Optional, Tuple

from loguru import logger
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from yt_database.config.settings import settings
from yt_database.gui.widgets.video_selection_table_widget import VideoSelectionTableWidget
from yt_database.services.protocols import ProjectManagerProtocol, TranscriptServiceProtocol


class BatchTranscriptionWidget(QWidget):
    # Signale korrigiert: Unterscheidung zwischen Request und Response
    channel_videos_requested = Signal(str)  # Sendet channel_url zum Laden
    videos_loaded = Signal(list)  # Empfängt geladene TranscriptData-Objekte
    batch_transcription_requested = Signal(str, int, str, list)  # channel_url, interval, provider, video_ids

    # Neue Signale für die VideoSelectionTable-Integration
    file_open_requested = Signal(str)  # Signal für das Öffnen von Dateien
    chapter_generation_requested = Signal(str)  # Signal für Kapitelgenerierung
    text_editor_open_requested = Signal(str)  # Signal für Text-Editor

    def __init__(
        self,
        pm_service: ProjectManagerProtocol,
        yt_service: TranscriptServiceProtocol,
        on_error: Callable[[str], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialisiert das Widget und seine Abhängigkeiten direkt."""
        super().__init__(parent)
        self._pm_service = pm_service
        self._transcript_service = yt_service
        self._on_error = on_error
        self._video_rows: List[Tuple[str, str, bool]] = []
        self._settings = settings

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Ruft die UI-Setup-Methoden in der richtigen Reihenfolge auf."""
        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self) -> None:
        """Initialisiert alle UI-Komponenten und konfiguriert ihre statischen Eigenschaften."""
        self.channel_url_input = QLineEdit()
        self.channel_url_input.setObjectName("channel_url_input")
        self.channel_url_input.setText(getattr(settings, "last_channel_url", "Kanal-URL eingeben..."))
        self.channel_url_input.setToolTip("Gib die URL des YouTube-Kanals ein (z.B. https://www.youtube.com/@99ZUEINS)")

        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setObjectName("interval_spinbox")
        self.interval_spinbox.setRange(1, 3600)
        self.interval_spinbox.setSuffix(" s")
        self.interval_spinbox.setValue(self._settings.default_interval)
        self.interval_spinbox.setToolTip("Intervall zwischen den Transkriptionen in Sekunden (1-3600)")

        self.max_videos_spinbox = QSpinBox()
        self.max_videos_spinbox.setObjectName("max_videos_spinbox")
        self.max_videos_spinbox.setRange(1, 1000)
        self.max_videos_spinbox.setSuffix(" Transcripts")
        self.max_videos_spinbox.setValue(self._settings.default_max_videos)
        self.max_videos_spinbox.setToolTip("Maximale Anzahl der Transcripts, die transkribiert werden sollen (1-1000)")

        self.provider_combo = QComboBox()
        self.provider_combo.setObjectName("provider_combo")
        self.provider_combo.addItem("YouTube API", "api")
        self.provider_combo.addItem("YT-DLP (experimentell)", "yt_dlp")
        self.provider_combo.setCurrentIndex(self.provider_combo.findData(self._settings.transcription_provider))
        self.provider_combo.setToolTip(
            "Wähle den Transkriptions-Provider: 'YouTube API' für offizielle API, 'YT-DLP' für experimentelle yt-dlp Unterstützung."
        )

        self.fetch_videos_button = QPushButton("Transcripts vom Kanal laden")
        self.fetch_videos_button.setObjectName("fetch_videos_button")
        self.fetch_videos_button.setToolTip(
            "Lädt die Metadaten aller Transcripts des angegebenen Kanals und zeigt sie in der Tabelle an."
        )

        self.start_transcription_button = QPushButton("Auswahl transkribieren")
        self.start_transcription_button.setObjectName("start_transcription_button")
        self.start_transcription_button.setEnabled(False)
        self.start_transcription_button.setToolTip(
            "Startet die Transkription der ausgewählten Videos. Wird aktiviert, sobald Videos ausgewählt sind."
        )

        self.transcription_progressbar = QProgressBar()
        self.transcription_progressbar.setObjectName("transcription_progressbar")
        self.transcription_progressbar.setVisible(False)
        self.transcription_progressbar.setToolTip("Zeigt den Fortschritt der laufenden Transkription an.")

        self.force_metadata_checkbox = QCheckBox("Channel-Metadaten immer neu laden")
        self.force_metadata_checkbox.setObjectName("force_metadata_checkbox")
        self.force_metadata_checkbox.setToolTip(
            "Wenn aktiviert, werden die Kanal-Metadaten immer neu vom Server geladen, auch wenn sie bereits gecacht sind."
        )

        self.video_selection_table = VideoSelectionTableWidget(project_manager_service=self._pm_service)
        self.video_selection_table.setObjectName("video_selection_table")
        self.video_selection_table.setToolTip(
            "Tabelle aller Videos des Kanals. Wähle die Videos aus, die transkribiert werden sollen."
        )

    def _setup_layouts(self) -> None:
        """Ordnet die initialisierten Widgets in Layouts an."""
        form_layout = QFormLayout()
        form_layout.addRow("Kanal-URL:", self.channel_url_input)
        form_layout.addRow("Intervall:", self.interval_spinbox)
        form_layout.addRow("Max. Transcripts:", self.max_videos_spinbox)
        form_layout.addRow("Provider:", self.provider_combo)
        form_layout.addRow(self.force_metadata_checkbox)

        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        vbox.addWidget(self.fetch_videos_button)
        vbox.addWidget(self.start_transcription_button)
        vbox.addWidget(self.transcription_progressbar)
        vbox.addWidget(self.video_selection_table)
        self.setLayout(vbox)

    def _setup_signals(self) -> None:
        """Verbindet die Signale der permanenten Widgets mit ihren Slots."""
        self.fetch_videos_button.clicked.connect(self._on_fetch_videos_clicked)
        self.start_transcription_button.clicked.connect(self._on_start_transcription_clicked)
        self.video_selection_table.video_selection_changed.connect(self.set_video_selection)

        # Signale für Kontextmenü-Funktionen weiterleiten
        self.video_selection_table.file_open_requested.connect(self.file_open_requested.emit)
        self.video_selection_table.chapter_generation_requested.connect(self.chapter_generation_requested.emit)
        self.video_selection_table.text_editor_open_requested.connect(self.text_editor_open_requested.emit)

    def _on_videos_fetched(self, transcripts: list) -> None:
        """Callback für das videos_fetched-Signal des Workers."""
        self.video_selection_table.set_videos(transcripts)
        self.videos_loaded.emit(transcripts)

    def _on_worker_finished(self) -> None:
        """Callback für das finished-Signal des Workers."""
        self.fetch_videos_button.setEnabled(True)
        self.fetch_videos_button.setText("Transcripts vom Kanal laden")

    @Slot()
    def _on_fetch_videos_clicked(self) -> None:
        """
        Signalisiert dem MainWindow, dass Transcripts für einen Kanal geladen werden sollen.
        """
        channel_url = self.channel_url_input.text().strip()
        if not channel_url:
            self._on_error("Bitte eine gültige Kanal-URL eingeben.")
            return

        # UI-Feedback, Button deaktivieren
        self.fetch_videos_button.setEnabled(False)
        self.fetch_videos_button.setText("Lade...")
        self.channel_videos_requested.emit(channel_url)

    def set_video_selection(self, selected_ids: List[str]) -> None:
        """Aktiviert/Deaktiviert den Start-Button je nach Auswahl."""
        logger.debug(f"BatchTranscriptionWidget: Video selection changed, {len(selected_ids)} IDs empfangen")
        self.start_transcription_button.setEnabled(bool(selected_ids))

    def on_videos_loaded(self, video_data: List) -> None:
        """
        Empfängt geladene Transcript-Daten vom MainWindow und zeigt sie in der Tabelle an.

        Args:
            video_data (List): Liste von TranscriptData-Objekten oder Transcript-Metadaten
        """
        self.video_selection_table.set_videos(video_data)
        self.videos_loaded.emit(video_data)  # Weiterleitung für andere Listener

        # UI-Feedback zurücksetzen
        self.fetch_videos_button.setEnabled(True)
        self.fetch_videos_button.setText("Transcripts vom Kanal laden")

    def get_selected_video_ids(self) -> List[str]:
        """Gibt die aktuell ausgewählten Transcript-IDs zurück."""
        return self.video_selection_table.get_selected_video_ids()

    def set_ui_for_running_state(self, is_running: bool) -> None:
        """
        Passt die Benutzeroberfläche an, je nachdem, ob ein Prozess läuft.
        Wenn ein Prozess läuft (is_running=True), werden die Eingabefelder und
        Buttons deaktiviert, um weitere Interaktionen zu verhindern. Die
        Fortschrittsanzeige wird sichtbar.
        Args:
            is_running (bool): True, wenn ein Prozess startet, False, wenn er endet.
        """
        # Deaktiviere alle Eingabefelder, um Änderungen während des Laufs zu verhindern
        self.channel_url_input.setEnabled(not is_running)
        self.interval_spinbox.setEnabled(not is_running)
        self.max_videos_spinbox.setEnabled(not is_running)
        self.provider_combo.setEnabled(not is_running)
        self.force_metadata_checkbox.setEnabled(not is_running)

        # Deaktiviere den Button zum Laden von Transcripts
        self.fetch_videos_button.setEnabled(not is_running)

        # Steuere den Haupt-Button und die Fortschrittsanzeige
        self.start_transcription_button.setEnabled(not is_running)
        self.transcription_progressbar.setVisible(is_running)

        if is_running:
            # Setze den Button-Text und die Fortschrittsanzeige zurück
            self.start_transcription_button.setText("Verarbeite...")
            self.transcription_progressbar.setValue(0)
        else:
            # Setze den Button-Text auf den Standardwert zurück
            self.start_transcription_button.setText("Auswahl transkribieren")
            # Der Button bleibt deaktiviert, bis eine neue Auswahl getroffen wird
            self.start_transcription_button.setEnabled(bool(self.get_selected_video_ids()))

    @Slot()
    def _on_start_transcription_clicked(self) -> None:
        """Signalisiert dem MainWindow, dass die Batch-Transkription gestartet werden soll."""
        logger.debug("Transkribieren-Button wurde geklickt. IDs: {}", self.get_selected_video_ids())
        self.batch_transcription_requested.emit(
            self.channel_url, self.interval, self.provider, self.get_selected_video_ids()
        )

    # Properties für Zugriff von außen (optional, für bessere Kapselung)
    @property
    def channel_url(self) -> str:
        """Gibt die aktuelle Kanal-URL zurück."""
        return self.channel_url_input.text().strip()

    @property
    def interval(self) -> int:
        """Gibt das aktuelle Intervall zurück."""
        return self.interval_spinbox.value()

    @property
    def max_videos(self) -> int:
        """Gibt die maximale Videoanzahl zurück."""
        return self.max_videos_spinbox.value()

    @property
    def provider(self) -> str:
        """Gibt den aktuellen Provider zurück."""
        return self.provider_combo.currentData()

    @property
    def force_metadata(self) -> bool:
        """Gibt zurück, ob die Checkbox für Metadaten-Reload gesetzt ist."""
        return self.force_metadata_checkbox.isChecked()

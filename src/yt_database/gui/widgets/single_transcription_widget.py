# src/yt_database/gui/widgets/single_transcription_widget.py
from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class SingleTranscriptionWidget(QWidget):
    """
    Widget für die Einzeltranskription von YouTube-Videos.
    Benötigt sowohl eine Transcript-ID/URL als auch den @-Handle des Kanals.

    Signals:
        transcriptionRequested(str, str): Wird ausgelöst mit (video_id_or_url, channel_handle).
    """

    transcriptionRequested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._initialize_widgets()
        self._initialize_layouts()
        self._connect_signals_slots()

    def _initialize_widgets(self):
        """Initialisiert alle UI-Komponenten."""
        self.video_input = QLineEdit()
        self.video_input.setPlaceholderText("Transcript-ID oder YouTube-URL eingeben...")

        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("@channelhandle eingeben...")

        self.button = QPushButton("Transkribieren")
        self.button.setEnabled(False)

        self.status_label = QLabel("Bereit.")
        self.status_label.setStyleSheet("color: gray;")

    def _initialize_layouts(self):
        """Ordnet die Widgets im Layout an."""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.addRow("Transcript-ID oder URL:", self.video_input)
        form_layout.addRow("Channel Handle:", self.channel_input)

        layout.addLayout(form_layout)
        layout.addWidget(self.button)
        layout.addWidget(self.status_label)
        layout.addStretch()

    def _connect_signals_slots(self):
        """Verbindet die Signale der Widgets mit den Slots."""
        self.video_input.textChanged.connect(self._on_text_changed)
        self.channel_input.textChanged.connect(self._on_text_changed)
        self.button.clicked.connect(self._on_button_clicked)

    def set_ui_for_running_state(self, is_running: bool) -> None:
        """Passt die UI an, je nachdem, ob ein Prozess läuft."""
        self.video_input.setEnabled(not is_running)
        self.channel_input.setEnabled(not is_running)
        self.button.setEnabled(not is_running)

        if is_running:
            self.button.setText("Verarbeite...")
            self.status_label.setText("Starte Transkription...")
        else:
            self.button.setText("Transkribieren")
            self.status_label.setText("Bereit.")
            # Stelle sicher, dass der Button-Status nach dem Lauf korrekt ist
            self._on_text_changed()

    def update_status_label(self, text: str) -> None:
        """Aktualisiert das Status-Label."""
        if hasattr(self, "status_label"):
            self.status_label.setText(text)
            logger.debug(f"Status-Update: {text}")

    def _on_text_changed(self):
        """Aktiviert den Button nur, wenn beide Felder gültig ausgefüllt sind."""
        video_ok = bool(self.video_input.text().strip())
        channel_ok = bool(self.channel_input.text().strip().startswith("@"))
        self.button.setEnabled(video_ok and channel_ok)

    def _on_button_clicked(self):
        """Sendet das Signal mit den Werten aus beiden Eingabefeldern."""
        video_text = self.video_input.text().strip()
        channel_text = self.channel_input.text().strip()
        if video_text and channel_text:
            self.transcriptionRequested.emit(video_text, channel_text)

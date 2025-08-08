"""
Prototyp für ein LogWidget mit ColoredLogEditor-Funktionalität.
PEP8, Google-Style Docstring, Typisierung.
"""

from __future__ import annotations

from loguru import logger  # noqa: F401
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


class LogWidget(QWidget):
    """Widget für die Anzeige von farbigen Logs."""

    # --- Konstanten für Log-Level-Farben ---
    LEVEL_COLORS = {
        "INFO": QColor("#4CAF50"),  # Grün
        "WARNING": QColor("#FFC107"),  # Gelb
        "ERROR": QColor("#F44336"),  # Rot
        "CRITICAL": QColor("#9C27B0"),  # Magenta
        "DEBUG": QColor("#00BCD4"),  # Cyan
    }
    CONTEXT_COLOR = QColor("#00bcd4")  # Cyan
    DEFAULT_COLOR = QColor("#a9b7c6")  # Grau/Weiß

    # --- Signale ---
    log_received = Signal(str, str)  # level, message

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Ruft die UI-Setup-Methoden in der richtigen Reihenfolge auf."""
        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self) -> None:
        """Initialisiert alle UI-Komponenten und konfiguriert ihre statischen Eigenschaften."""
        self.label = QLabel("Log-Ansicht (Prototyp mit Farbunterstützung)")
        self.label.setObjectName("log_widget_label")

        self.log_text = QPlainTextEdit()
        self.log_text.setObjectName("log_widget_textedit")
        self.log_text.setPlaceholderText("Hier werden farbige Logs angezeigt ...")
        self.log_text.setMinimumHeight(300)
        self.log_text.setReadOnly(True)

        # Font und Styling
        font = QFont("Courier", 10)
        self.log_text.setFont(font)
        self.log_text.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6;")

        self.clear_btn = QPushButton("Log löschen")
        self.clear_btn.setObjectName("log_widget_clear_btn")

    def _setup_layouts(self) -> None:
        """Ordnet die initialisierten Widgets in Layouts an."""
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.log_text)
        layout.addWidget(self.clear_btn)
        self.setLayout(layout)

    def _setup_signals(self) -> None:
        """Verbindet die Signale der permanenten Widgets mit ihren Slots."""
        self.clear_btn.clicked.connect(self.clear_log)

    @Slot(str, str)
    def receive_log(self, level: str, message: str) -> None:
        """Slot, um Log-Nachrichten (Level, Text) zu empfangen und darzustellen."""
        self.append_log(message, level)
        self.log_received.emit(level, message)

    def append_log(self, message: str, level: str = "INFO") -> None:
        """Färbt und fügt eine formatierte Log-Nachricht hinzu."""
        segments = message.split("|", 3)
        if len(segments) == 4:
            time_str, level_str, context_str, msg_str = [s.strip() for s in segments]
        else:
            # Fallback: alles grau
            time_str, level_str, context_str, msg_str = "", level, "", message

        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Zeitstempel (grau/weiß)
        fmt_time = QTextCharFormat()
        fmt_time.setForeground(self.DEFAULT_COLOR)
        cursor.insertText(f"{time_str} | ", fmt_time)

        # Level (farbig)
        fmt_level = QTextCharFormat()
        fmt_level.setForeground(self.LEVEL_COLORS.get(level_str, self.DEFAULT_COLOR))
        cursor.insertText(f"{level_str}", fmt_level)
        cursor.insertText(" | ", fmt_time)

        # Kontext (cyan)
        fmt_context = QTextCharFormat()
        fmt_context.setForeground(self.CONTEXT_COLOR)
        cursor.insertText(f"{context_str}", fmt_context)
        cursor.insertText(" | ", fmt_time)

        # Nachricht (grau/weiß)
        fmt_msg = QTextCharFormat()
        fmt_msg.setForeground(self.DEFAULT_COLOR)
        cursor.insertText(f"{msg_str}\n", fmt_msg)

        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()

    @Slot()
    def clear_log(self) -> None:
        """Löscht alle Log-Einträge."""
        self.log_text.clear()

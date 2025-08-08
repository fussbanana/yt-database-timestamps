"""
Dialog zur Anzeige und Bearbeitung von Dateiinhalten mit Speichern-Funktion.

Dieses Modul stellt einen einfachen Editor-Dialog bereit, der den Inhalt einer Datei anzeigt und Änderungen direkt zurückschreiben kann.
Enthält strategische Debug-Logs und Entwickler-Kommentare für bessere Nachvollziehbarkeit.
"""

import os
from typing import Optional

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TextFileEditorWidget(QWidget):
    """Widget zur Anzeige und Bearbeitung von Dateiinhalten mit Speichern-Funktion."""

    # --- Signale für externe Kommunikation ---
    fileSaved = Signal(str)  # Signal mit dem Dateipfad, wenn gespeichert wurde
    widgetClosed = Signal()  # Signal, wenn das Widget geschlossen wird

    def __init__(
        self, title: str = "", content: str = "", file_path: str = "", parent: Optional[QWidget] = None
    ) -> None:
        """Initialisiert das Widget und seine Daten."""
        super().__init__(parent)
        logger.debug(f"FileViewerDialog aufgerufen mit title={title}, file_path={file_path}")

        # Daten im Konstruktor speichern
        self._title = title
        self._content = content
        self._file_path = file_path
        self._window: Optional[QMainWindow] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Ruft die UI-Setup-Methoden in der richtigen Reihenfolge auf."""
        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self) -> None:
        """Initialisiert alle UI-Komponenten und konfiguriert ihre statischen Eigenschaften."""
        self.setWindowTitle(self._title if self._title else "Datei-Editor")
        self.setMinimumSize(600, 800)

        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setObjectName("text_file_editor_text_edit")
        self.text_edit.setPlainText(self._content)
        self.text_edit.setReadOnly(False)

        self.save_button = QPushButton("Speichern")
        self.save_button.setObjectName("text_file_editor_save_button")

        self.close_button = QPushButton("Schließen")
        self.close_button.setObjectName("text_file_editor_close_button")

    def _setup_layouts(self) -> None:
        """Ordnet die initialisierten Widgets in Layouts an."""
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.text_edit)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def _setup_signals(self) -> None:
        """Verbindet die Signale der permanenten Widgets mit ihren Slots."""
        self.save_button.clicked.connect(self._on_save_clicked)
        self.close_button.clicked.connect(self._on_close_clicked)

    def _on_save_clicked(self) -> None:
        """
        Validiert und speichert den aktuellen Inhalt. Sendet fileSaved-Signal bei Erfolg.
        """
        logger.debug(f"FileViewerDialog._on_save_clicked() aufgerufen für {self._file_path}")
        if not self._file_path:
            QMessageBox.warning(self, "Fehler", "Kein Dateipfad zum Speichern vorhanden.")
            return
        try:
            with open(self._file_path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            logger.debug(f"Datei erfolgreich gespeichert: {self._file_path}")
            QMessageBox.information(self, "Erfolg", f"Datei erfolgreich gespeichert: {self._file_path}")
            self.fileSaved.emit(self._file_path)
        except Exception as e:
            logger.error(f"Fehler beim Speichern von {self._file_path}: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {e}")

    def _on_close_clicked(self) -> None:
        """
        Sendet das widgetClosed-Signal und schließt ggf. das Fenster.
        """
        self.widgetClosed.emit()
        # Wenn als Fenster angezeigt, schließe das Fenster
        if self._window is not None:
            self._window.close()
            self._window = None
        else:
            # Wenn im MainWindow eingebettet, einfach ausblenden oder schließen
            self.close()

    def load_file(self, file_path: str) -> None:
        """
        Lädt eine neue Datei in den Editor.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            self._file_path = file_path
            self._content = content
            self.text_edit.setPlainText(content)

            # Update window title
            self.setWindowTitle(f"Text Editor - {os.path.basename(file_path)}")
            if self._window:
                self._window.setWindowTitle(self.windowTitle())

            logger.debug(f"Datei geladen: {file_path}")

        except Exception as e:
            logger.error(f"Fehler beim Laden von {file_path}: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Datei: {e}")

    def show_as_window(self) -> None:
        """
        Zeigt das Editor-Widget als eigenständiges, nicht-modales Fenster an.
        """
        if self._window is None:
            self._window = QMainWindow()
            self._window.setCentralWidget(self)
            self._window.setWindowTitle(self.windowTitle())
            self._window.resize(800, 600)
        self._window.show()
        self._window.activateWindow()
        self._window.raise_()

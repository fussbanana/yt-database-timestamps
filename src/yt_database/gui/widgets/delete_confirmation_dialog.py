"""
Bestätigungsdialog für Löschvorgänge mit Statistiken und Sicherheitsabfragen.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from yt_database.gui.utils.icons import Icons


class DeleteConfirmationDialog(QDialog):
    """Sicherheitsdialog mit detaillierten Statistiken vor Löschung."""

    def __init__(self, delete_type: str, preview_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{delete_type} löschen - Bestätigung erforderlich")
        self.setModal(True)
        self.setMinimumWidth(400)

        self.preview_data = preview_data
        self.setup_ui(delete_type)

    def setup_ui(self, delete_type: str):
        """Erstellt die UI-Elemente des Dialogs."""
        layout = QVBoxLayout(self)

        # Warnung Header

        warning_widget = QWidget()
        warning_layout = QHBoxLayout(warning_widget)
        warning_layout.setContentsMargins(0, 0, 0, 0)

        warning_icon_label = QLabel()
        warning_icon = Icons.get(Icons.ALERT)
        warning_icon_label.setPixmap(warning_icon.pixmap(16, 16))

        warning_text_label = QLabel("ACHTUNG: Diese Aktion kann nicht rückgängig gemacht werden!")
        warning_text_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px; padding: 10px;")
        warning_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        warning_layout.addWidget(warning_icon_label)
        warning_layout.addWidget(warning_text_label)
        warning_layout.addStretch()

        layout.addWidget(warning_widget)

        # Statistiken anzeigen
        if self.preview_data.get("success"):
            stats_widget = self._create_stats_widget(delete_type)
            layout.addWidget(stats_widget)
        else:
            error_widget = QWidget()
            error_layout = QHBoxLayout(error_widget)
            error_layout.setContentsMargins(0, 0, 0, 0)

            error_icon_label = QLabel()
            error_icon = Icons.get(Icons.X_CIRCLE)
            error_icon_label.setPixmap(error_icon.pixmap(16, 16))

            error_text_label = QLabel(f"Fehler: {self.preview_data.get('error', 'Unbekannter Fehler')}")
            error_text_label.setStyleSheet("color: red; padding: 10px;")

            error_layout.addWidget(error_icon_label)
            error_layout.addWidget(error_text_label)
            error_layout.addStretch()

            layout.addWidget(error_widget)

            # Nur Abbrechen-Button bei Fehlern
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
            button_box.rejected.connect(self.reject)
            layout.addWidget(button_box)
            return

        # Bestätigungs-Checkbox
        self.confirm_checkbox = QCheckBox("Ich verstehe, dass diese Aktion nicht rückgängig gemacht werden kann")
        self.confirm_checkbox.setStyleSheet("font-weight: bold; margin: 10px;")
        self.confirm_checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self.confirm_checkbox)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # OK-Button initial deaktiviert
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("Löschen")
        self.ok_button.setStyleSheet("color: red; font-weight: bold;")
        self.ok_button.setEnabled(False)

        layout.addWidget(self.button_box)

    def _create_stats_widget(self, delete_type: str) -> QWidget:
        """Erstellt das Widget mit den Löschungsstatistiken."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Titel des zu löschenden Items
        title_label = QLabel(f"{delete_type}: {self.preview_data.get('title', 'Unbekannt')}")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Kanal-Info (nur bei Video-Löschung)
        if delete_type == "Video" and "channel_name" in self.preview_data:
            channel_label = QLabel(f"{Icons.get(Icons.VIDEO).name} Kanal: {self.preview_data['channel_name']}")
            channel_label.setStyleSheet("margin-bottom: 5px;")
            layout.addWidget(channel_label)

        # Statistiken
        videos_affected = self.preview_data.get("videos_affected", 0)
        chapters_affected = self.preview_data.get("chapters_affected", 0)

        if videos_affected > 0:
            video_label = QLabel(f"{Icons.get(Icons.VIDEO).name} Videos: {videos_affected}")
            video_label.setStyleSheet("margin-bottom: 5px;")
            layout.addWidget(video_label)

        if chapters_affected > 0:
            chapter_label = QLabel(f"{Icons.get(Icons.BOOK).name} Kapitel: {chapters_affected}")
            chapter_label.setStyleSheet("margin-bottom: 5px;")
            layout.addWidget(chapter_label)

        # Warnung bei großen Löschungen
        if videos_affected > 10 or chapters_affected > 50:
            big_warning = QLabel(f"{Icons.get(Icons.WARNING).name} GROSSE LÖSCHUNG! Backup empfohlen!")
            big_warning.setStyleSheet("color: orange; font-weight: bold; margin-top: 10px;")
            layout.addWidget(big_warning)

        return widget

    def _on_checkbox_changed(self, state):
        """Aktiviert/deaktiviert den OK-Button basierend auf der Checkbox."""
        self.ok_button.setEnabled(state == Qt.CheckState.Checked.value)

    def is_confirmed(self) -> bool:
        """Gibt zurück, ob der Benutzer die Löschung bestätigt hat."""
        return self.result() == QDialog.DialogCode.Accepted and self.confirm_checkbox.isChecked()

"""
Production-Dashboard-Widget für YT Database Mission Control.
Zeigt Statis        self.progress_card, self.progress_card_title, self.progress_card_value, self.progress_card_desc = self._create_stat_card_widgets("Fortschritt", "Lade...", "Transkribiert", Icons.DATABASE)iken, Status und Schnellzugriffe an.
PEP8, Google-Style Docstring, Typisierung.
"""

from datetime import datetime
from typing import Any, Optional

from loguru import logger
from PySide6.QtCore import QTimer, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from yt_database.gui.utils.icons import Icons
from yt_database.services.service_factory import ServiceFactory


class DashboardWidget(QWidget):
    """Production Dashboard-Widget mit Statistiken, Status und Schnellzugriffen."""

    # Signale für Dashboard-Aktionen
    quick_batch_transcription_requested = Signal()
    quick_database_refresh_requested = Signal()
    quick_settings_requested = Signal()
    channel_analysis_requested = Signal()

    def __init__(self, service_factory: Optional[ServiceFactory] = None, parent: QWidget | None = None) -> None:
        """Initialisiert das Dashboard mit Service-Integration."""
        super().__init__(parent)
        self.service_factory = service_factory
        self._stats_cache: dict[str, Any] = {}

        self._setup_ui()
        self._setup_auto_refresh()
        self._refresh_stats()

    def _setup_ui(self) -> None:
        """Ruft die UI-Setup-Methoden in der richtigen Reihenfolge auf."""
        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self) -> None:
        """Initialisiert alle UI-Komponenten und konfiguriert ihre statischen Eigenschaften."""
        # --- Header ---
        self.title_label = QLabel("YT Database Mission Control")
        self.title_label.setObjectName("title_label")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.subtitle_label = QLabel("Dashboard & Steuerungszentrale")
        self.subtitle_label.setObjectName("subtitle_label")
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle_font.setItalic(True)
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setStyleSheet("color: gray; margin-bottom: 20px;")

        # --- Statistik-Karten (Frames und Labels) ---
        self.videos_card, self.videos_card_title, self.videos_card_value, self.videos_card_desc = (
            self._create_stat_card_widgets("Videos gesamt", "Lade...", "In der Datenbank erfasst", Icons.VIDEO)
        )
        self.transcribed_card, self.transcribed_card_title, self.transcribed_card_value, self.transcribed_card_desc = (
            self._create_stat_card_widgets("Transkribiert", "Lade...", "Erfolgreich verarbeitet", Icons.CHECK_CIRCLE)
        )
        self.chapters_card, self.chapters_card_title, self.chapters_card_value, self.chapters_card_desc = (
            self._create_stat_card_widgets("Mit Kapiteln", "Lade...", "Kapitel generiert", Icons.BOOK_OPEN)
        )
        self.channels_card, self.channels_card_title, self.channels_card_value, self.channels_card_desc = (
            self._create_stat_card_widgets("Kanäle", "Lade...", "Verschiedene Quellen", Icons.ARCHIVE)
        )
        self.duration_card, self.duration_card_title, self.duration_card_value, self.duration_card_desc = (
            self._create_stat_card_widgets("Gesamtdauer", "Lade...", "Alle Videos zusammen", Icons.VOLUME)
        )
        self.progress_card, self.progress_card_title, self.progress_card_value, self.progress_card_desc = (
            self._create_stat_card_widgets("� Fortschritt", "Lade...", "Transkribiert")
        )

        # --- Schnellzugriffe ---
        self.quick_batch_btn = QPushButton("Batch-Transkription starten")
        self.quick_batch_btn.setIcon(Icons.get(":/icons/noto--check-mark-button.svg"))
        self.quick_batch_btn.setObjectName("quick_batch_btn")
        self.quick_batch_btn.setToolTip(
            "Öffnet das Batch-Transkriptions-Widget zum Verarbeiten mehrerer Videos auf einmal."
        )

        self.quick_refresh_btn = QPushButton("Datenbank aktualisieren")
        self.quick_refresh_btn.setIcon(Icons.get(":/icons/noto--bar-chart.svg"))
        self.quick_refresh_btn.setObjectName("quick_refresh_btn")
        self.quick_refresh_btn.setToolTip(
            "Lädt alle Dashboard-Statistiken neu und aktualisiert die Datenbank-Übersicht."
        )

        self.quick_settings_btn = QPushButton("Einstellungen öffnen")
        self.quick_settings_btn.setIcon(Icons.get(":/icons/settings.svg"))
        self.quick_settings_btn.setObjectName("quick_settings_btn")
        self.quick_settings_btn.setToolTip("Öffnet den Konfigurationsdialog für Anwendungseinstellungen.")

        self.quick_analysis_btn = QPushButton("Channel-Analyse")
        self.quick_analysis_btn.setObjectName("quick_analysis_btn")
        self.quick_analysis_btn.setIcon(Icons.get(":/icons/emojione-v1--lightning-mood.svg"))
        self.quick_analysis_btn.setToolTip(
            "Startet eine detaillierte Analyse der Kanal-Daten und Transkriptions-Qualität."
        )

        for btn in [self.quick_batch_btn, self.quick_refresh_btn, self.quick_settings_btn, self.quick_analysis_btn]:
            btn.setMinimumHeight(40)

        # --- Status-Bereich ---
        self.status_label = QLabel("System bereit")
        self.status_label.setObjectName("status_label")
        self.status_label.setToolTip("Zeigt den aktuellen Systemstatus und laufende Operationen an.")

        self.last_update_label = QLabel("Letzte Aktualisierung: Nie")
        self.last_update_label.setObjectName("last_update_label")
        self.last_update_label.setToolTip("Zeitpunkt der letzten Dashboard-Aktualisierung.")

        # --- Fortschritts-Anzeigen ---
        self.progress_label = QLabel("Aktuelle Operationen:")
        self.progress_label.setObjectName("progress_label")
        self.progress_label.setToolTip("Informationen über aktuell laufende Hintergrundprozesse.")

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setToolTip("Fortschritt aktueller Operationen (z.B. Transkriptionen).")

        self.progress_text = QLabel("")
        self.progress_text.setObjectName("progress_text")
        self.progress_text.setToolTip("Detaillierte Beschreibung der aktuellen Operation.")

    def _create_stat_card_widgets(
        self, title: str, value: str, description: str, icon_path: str | None = None
    ) -> tuple[QFrame, QWidget, QLabel, QLabel]:
        """Erstellt die Widgets für eine einzelne Statistik-Karte (ohne Layout)."""
        from PySide6.QtWidgets import QHBoxLayout, QWidget

        card = QFrame()
        card.setObjectName(f"card_{title.replace(' ', '_').lower()}")
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setLineWidth(1)

        # Container für Icon + Text
        if icon_path:
            title_container = QWidget()
            title_layout = QHBoxLayout(title_container)
            title_layout.setContentsMargins(0, 0, 0, 0)
            title_layout.setSpacing(5)

            # Icon Label
            icon_label = QLabel()
            icon_label.setPixmap(Icons.get(icon_path).pixmap(16, 16))
            title_layout.addWidget(icon_label)

            # Text Label
            title_label = QLabel(title)
            title_layout.addWidget(title_label)
            title_layout.addStretch()

            # Verwende das Container-Widget anstelle des Labels
            title_widget = title_container
        else:
            title_label = QLabel(title)
            title_widget = title_label

        title_label.setObjectName(f"stat_card_title_{title.replace(' ', '_').lower()}")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)

        value_label = QLabel(value)
        value_label.setObjectName(f"stat_card_value_{title.replace(' ', '_').lower()}")
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)

        desc_label = QLabel(description)
        desc_label.setObjectName(f"stat_card_desc_{title.replace(' ', '_').lower()}")
        desc_label.setStyleSheet("color: gray; font-size: 10px;")

        return card, title_widget, value_label, desc_label

    def _setup_layouts(self) -> None:
        """Organisiert alle initialisierten Widgets im Layout."""
        # Hauptlayout mit ScrollArea
        main_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setObjectName("scroll_area")
        scroll_widget = QWidget()
        scroll_widget.setObjectName("scroll_widget")
        scroll_layout = QVBoxLayout(scroll_widget)

        # Header-Bereich
        header_layout = QVBoxLayout()
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.subtitle_label)

        # Statistik-Karten in Grid
        stats_group = QGroupBox("Aktuelle Statistiken")
        stats_group.setObjectName("stats_group")
        stats_layout = QGridLayout(stats_group)

        # Layout für jede Karte erstellen und Widgets hinzufügen
        for card, title, value, desc in [
            (self.videos_card, self.videos_card_title, self.videos_card_value, self.videos_card_desc),
            (
                self.transcribed_card,
                self.transcribed_card_title,
                self.transcribed_card_value,
                self.transcribed_card_desc,
            ),
            (self.chapters_card, self.chapters_card_title, self.chapters_card_value, self.chapters_card_desc),
            (self.channels_card, self.channels_card_title, self.channels_card_value, self.channels_card_desc),
            (self.duration_card, self.duration_card_title, self.duration_card_value, self.duration_card_desc),
            (self.progress_card, self.progress_card_title, self.progress_card_value, self.progress_card_desc),
        ]:
            card_layout = QVBoxLayout(card)
            card_layout.addWidget(title)
            card_layout.addWidget(value)
            card_layout.addWidget(desc)
            card_layout.addStretch()

        # Karten dem Grid-Layout hinzufügen
        stats_layout.addWidget(self.videos_card, 0, 0)
        stats_layout.addWidget(self.transcribed_card, 0, 1)
        stats_layout.addWidget(self.chapters_card, 0, 2)
        stats_layout.addWidget(self.channels_card, 1, 0)
        stats_layout.addWidget(self.duration_card, 1, 1)
        stats_layout.addWidget(self.progress_card, 1, 2)

        # Schnellzugriffe
        actions_group = QGroupBox("Schnellzugriffe")
        actions_group.setObjectName("actions_group")
        actions_layout = QGridLayout(actions_group)
        actions_layout.addWidget(self.quick_batch_btn, 0, 0)
        actions_layout.addWidget(self.quick_refresh_btn, 0, 1)
        actions_layout.addWidget(self.quick_settings_btn, 1, 0)
        actions_layout.addWidget(self.quick_analysis_btn, 1, 1)

        # Status-Bereich
        status_group = QGroupBox("System-Status")
        status_group.setObjectName("status_group")
        status_layout = QVBoxLayout(status_group)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.last_update_label)
        status_layout.addWidget(self.progress_label)
        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.progress_text)

        # Alles zusammenfügen
        scroll_layout.addLayout(header_layout)
        scroll_layout.addWidget(stats_group)
        scroll_layout.addWidget(actions_group)
        scroll_layout.addWidget(status_group)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

    def _setup_signals(self) -> None:
        """Verbindet die Signale der permanenten Widgets mit ihren Slots."""
        self.quick_batch_btn.clicked.connect(self.quick_batch_transcription_requested.emit)
        self.quick_refresh_btn.clicked.connect(self.quick_database_refresh_requested.emit)
        self.quick_settings_btn.clicked.connect(self.quick_settings_requested.emit)
        self.quick_analysis_btn.clicked.connect(self.channel_analysis_requested.emit)

    def _setup_auto_refresh(self) -> None:
        """Richtet automatische Aktualisierung der Statistiken ein."""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_stats)
        self.refresh_timer.start(30000)  # Alle 30 Sekunden

    @Slot()
    def _refresh_stats(self) -> None:
        """Aktualisiert alle Statistiken aus der Datenbank."""
        if not self.service_factory:
            logger.debug("Keine ServiceFactory verfügbar für Statistiken.")
            return

        try:
            pm_service = self.service_factory.get_project_manager_service()

            # Direkter Zugriff auf die Datenbank für bessere Performance
            from yt_database.database import Channel, Transcript

            # Grundstatistiken
            total_videos = Transcript.select().count()
            transcribed_videos = Transcript.select().where(Transcript.is_transcribed).count()
            videos_with_chapters = Transcript.select().where(Transcript.has_chapters).count()
            total_channels = Channel.select().count()

            # Dauer-Berechnungen
            total_duration_query = Transcript.select().where(Transcript.duration.is_null(False))
            total_duration_seconds = 0
            for video in total_duration_query:
                if video.duration:
                    try:
                        # Versuche duration als int zu behandeln, falls es ein String ist
                        duration_val = int(video.duration) if isinstance(video.duration, str) else video.duration
                        total_duration_seconds += duration_val
                    except (ValueError, TypeError):
                        # Ignoriere ungültige duration-Werte
                        continue
            total_duration_hours = total_duration_seconds / 3600 if total_duration_seconds else 0

            # Prozentberechnung
            transcription_progress = (transcribed_videos / total_videos * 100) if total_videos > 0 else 0
            chapters_progress = (videos_with_chapters / total_videos * 100) if total_videos > 0 else 0

            # Werte in die Labels schreiben
            self.videos_card_value.setText(str(total_videos))
            self.transcribed_card_value.setText(f"{transcribed_videos} ({transcription_progress:.1f}%)")
            self.chapters_card_value.setText(f"{videos_with_chapters} ({chapters_progress:.1f}%)")
            self.channels_card_value.setText(str(total_channels))

            # Dauer formatiert anzeigen
            if total_duration_hours >= 1:
                self.duration_card_value.setText(f"{total_duration_hours:.1f}h")
            else:
                self.duration_card_value.setText(f"{total_duration_seconds // 60:.0f}min")

            # Fortschritt in einfacher Form
            self.progress_card_value.setText(f"{transcription_progress:.0f}%")

            # Status aktualisieren
            self.last_update_label.setText(f"Letzte Aktualisierung: {datetime.now().strftime('%H:%M:%S')}")

            # Status basierend auf Daten
            if total_videos == 0:
                self.status_label.setText("Keine Videos in der Datenbank")
            elif transcribed_videos == total_videos:
                self.status_label.setText("Alle Videos vollständig transkribiert")
            else:
                remaining = total_videos - transcribed_videos
                self.status_label.setText(f"{remaining} Videos noch zu transkribieren")

            logger.debug("Dashboard-Statistiken aktualisiert.")

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Dashboard-Statistiken: {e}")
            self.status_label.setText("Fehler beim Laden der Statistiken")
            # Fallback-Werte bei Fehlern
            for card_value in [
                self.videos_card_value,
                self.transcribed_card_value,
                self.chapters_card_value,
                self.channels_card_value,
                self.duration_card_value,
                self.progress_card_value,
            ]:
                card_value.setText("Fehler")

    @Slot()
    def set_progress(self, text: str, value: int = -1) -> None:
        """Zeigt Fortschritt für laufende Operationen."""
        self.progress_text.setText(text)
        if value >= 0:
            self.progress_bar.setValue(value)
            self.progress_bar.setVisible(True)
        else:
            self.progress_bar.setVisible(False)

    @Slot()
    def clear_progress(self) -> None:
        """Versteckt die Fortschrittsanzeige."""
        self.progress_bar.setVisible(False)
        self.progress_text.setText("")

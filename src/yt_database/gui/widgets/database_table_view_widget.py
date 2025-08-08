#
# DatabaseOverviewWidget: Übersicht und Filter für Kanäle und Transcripts aus der Datenbank.
# Zeigt alle Kanäle und Transcripts tabellarisch, unterstützt Filterung und Refresh.

import os

from loguru import logger
from PySide6.QtCore import QEvent, QSortFilterProxyModel, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QDesktopServices, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QProgressBar,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from yt_database.database import Transcript
from yt_database.gui.utils.icons import Icons
from yt_database.gui.widgets.delete_confirmation_dialog import DeleteConfirmationDialog


class DatabaseOverviewWidget(QWidget):
    file_open_requested = Signal(str)
    chapter_generation_requested = Signal(str)
    # Signals
    single_transcription_requested = Signal(str, str, bool)  # video_id, channel_handle, force_download
    batch_transcription_requested = Signal(list)  # [video_ids] für Batch-Processing
    text_editor_open_requested = Signal(str)  # video_id für Text-Editor

    def __init__(self, project_manager_service, parent=None):
        super().__init__(parent)
        self.pm_service = project_manager_service
        self.parent_window = parent  # Referenz für WorkerManager

        self._setup_ui()

        self._setup_columns()
        self.refresh_data()

    def _setup_ui(self):
        """Ruft die UI-Setup-Methoden in der richtigen Reihenfolge auf."""
        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self):
        """Initialisiert alle UI-Komponenten und konfiguriert ihre statischen Eigenschaften."""
        self.model = QStandardItemModel(self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(-1)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.table_view = QTableView(self)
        self.table_view.setObjectName("database_overview_table_view")
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.setItemDelegateForColumn(10, HyperlinkDelegate(self.table_view))  # Video-URL

        # Header-Einstellungen
        self.table_view.setColumnWidth(0, 400)  # Setzt die erste Spalte auf 400 Pixel Breite
        self.table_view.setColumnWidth(1, 200)  # Setzt die zweite Spalte auf 200 Pixel Breite

        # MULTI-SELECTION aktivieren
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)

        # Progress Bar für asynchrones Laden
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setObjectName("database_overview_progress_bar")
        self.progress_bar.setVisible(False)

        # Suchleiste
        self.search_label = QLabel("Suche:")
        self.search_label.setObjectName("database_overview_search_label")
        self.search_input = QLineEdit(self)
        self.search_input.setObjectName("database_overview_search_input")
        self.search_input.setPlaceholderText("Transcripts durchsuchen...")

    def _setup_layouts(self):
        """Ordnet die initialisierten Widgets in Layouts an."""
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_input)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table_view)
        self.setLayout(main_layout)

    def _setup_signals(self):
        """Verbindet die Signale der permanenten Widgets mit ihren Slots."""
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        self.search_input.textChanged.connect(self.filter_videos)

    def _setup_columns(self):
        self.model.setHorizontalHeaderLabels(
            [
                "Videotitel",  # 0
                "Video-ID",  # 1
                "Dauer",  # 3
                "Kapitel (einfach)",  # 4
                "Kapitel (detailliert)",  # 5
                "Transkriptzeilen",  # 6
                # "Kanal-ID",  # 7
                # "Kanalname",  # 8
                # "Kanal-URL",  # 9
                "Kapitel",  # 7
                "Transkribiert",  # 8
                "Veröffentlichungsdatum",  # 9
                "Kanal-Handle",  # 10
                "Video-URL",  # 11
                "Fehlergrund",  # 12
            ]
        )

    def _create_row_items_for_enriched_video(self, enriched_video: dict) -> list:
        """Erstellt Tabellenzeile für ein erweitertes Transcript-Objekt mit der neuen Datenbankarchitektur."""
        transcript = enriched_video["transcript"]
        has_transcript = enriched_video.get("has_transcript", False)
        has_chapters = enriched_video.get("has_chapters", False)

        # Channel-Daten aus der Relation holen
        channel = transcript.channel if hasattr(transcript, "channel") else None

        # Verwende Datenbank-Informationen für konsistente Anzeige
        db_transcribed = getattr(transcript, "is_transcribed", False)
        db_transcript_lines = getattr(transcript, "transcript_lines", 0)

        # Rechne die Dauer von Sekunden in ein lesbares Format um
        duration = getattr(transcript, "duration", 0)
        if isinstance(duration, int):
            hours, remainder = divmod(duration, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        else:
            duration_str = "00:00:00"

        title_item = QStandardItem(str(transcript.title))  # 0
        video_id_item = QStandardItem(str(transcript.video_id))  # 1
        duration_item = QStandardItem(duration_str)  # 2
        chapter_count_item = QStandardItem(str(getattr(transcript, "chapter_count", 0)))  # 3
        detailed_chapter_count_item = QStandardItem(str(getattr(transcript, "detailed_chapter_count", 0)))  # 4
        transcript_lines_item = QStandardItem(str(db_transcript_lines))  # 5
        chapter_item = QStandardItem("")  # 6
        if has_chapters:
            chapter_item.setIcon(Icons.get(Icons.CHECK))
        transcribed_item = QStandardItem("")  # 7
        if has_transcript:
            transcribed_item.setIcon(Icons.get(Icons.CHECK))
        publish_date_item = QStandardItem(str(transcript.publish_date))  # 8
        channel_handle_item = QStandardItem(str(getattr(channel, "handle", "")) if channel else "")  # 9
        video_url_item = QStandardItem(str(transcript.video_url))  # 10
        error_reason_item = QStandardItem(str(getattr(transcript, "error_reason", "")))  # 11

        transcribed_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        chapter_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        chapter_count_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
        detailed_chapter_count_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
        transcript_lines_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
        duration_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)

        return [
            title_item,  # 0
            video_id_item,  # 1
            duration_item,  # 2
            chapter_count_item,  # 3
            detailed_chapter_count_item,  # 4
            transcript_lines_item,  # 5
            chapter_item,  # 6
            transcribed_item,  # 7
            publish_date_item,  # 8
            channel_handle_item,  # 9
            video_url_item,  # 10
            error_reason_item,  # 11
        ]

    def refresh_data(self):
        """Lädt Transcripts synchron (ohne Threading um Crashes zu vermeiden)."""
        try:
            logger.debug("DatabaseOverviewWidget: Starte direktes Laden der Transcripts")

            # Zeige Progress Bar
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress

            # Lade Transcripts direkt ohne Threading (um Crashes zu vermeiden)
            logger.debug("DatabaseOverviewWidget: Lade Transcripts aus Datenbank (ohne Threading)")
            try:
                # Lade Transcripts mit Channel-Relationen
                from yt_database.database import Channel

                transcripts = list(Transcript.select().join(Channel))
                self._adjust_column_sizes()
                logger.debug(f"DatabaseOverviewWidget: {len(transcripts)} Transcripts aus DB geladen")
            except Exception as e:
                logger.error(f"Datenbankfehler beim Laden der Transcripts: {e}")
                self.progress_bar.setVisible(False)
                self._load_videos_sync()
                return

            if not transcripts:
                logger.debug("DatabaseOverviewWidget: Keine Transcripts in der Datenbank gefunden")
                self.progress_bar.setVisible(False)
                return

            # Erstelle Worker für Transcript-Verarbeitung OHNE Threading
            logger.debug("DatabaseOverviewWidget: Verarbeite Transcript-Status ohne Threading")

            # Direct processing without worker threads
            enriched_videos = []
            total_videos = len(transcripts)

            # Verarbeite Transcripts direkt mit Datenbank-Werten (kein Dateisystem-Check nötig)
            logger.debug("DatabaseOverviewWidget: Verwende Datenbank-Status für Transcript-Informationen")

            # Progress-Updates
            batch_size = 100
            for i, transcript in enumerate(transcripts):
                try:
                    if not hasattr(transcript, "video_id") or not transcript.video_id:
                        continue

                    # Direct processing mit Datenbank-Werten
                    enriched_video = self._create_enriched_video_with_batch_info(transcript, {})
                    enriched_videos.append(enriched_video)

                except Exception as e:
                    logger.debug(f"Fehler bei Transcript {getattr(transcript, 'video_id', 'unknown')}: {e}")
                    continue

                # Progress-Update
                if (i + 1) % batch_size == 0 or (i + 1) == total_videos:
                    self.progress_bar.setRange(0, total_videos)
                    self.progress_bar.setValue(i + 1)
                    # Process events to keep GUI responsive
                    QApplication.processEvents()

            logger.debug(f"DatabaseOverviewWidget: {len(enriched_videos)} Transcripts erfolgreich verarbeitet")

            # Populate table directly
            self._populate_table_with_videos(enriched_videos)
            self.progress_bar.setVisible(False)

        except Exception as e:
            logger.error(f"Fehler beim Laden der Transcripts: {e}")
            self.progress_bar.setVisible(False)
            self._load_videos_sync()

    def _batch_check_transcript_directories(self, channel_ids: set) -> dict:
        """Überprüft effizient alle Transcript-Verzeichnisse für die gegebenen Channel-IDs."""
        transcript_info = {}

        try:
            # Hole Projektverzeichnis aus den Settings
            if hasattr(self.pm_service, "settings") and hasattr(self.pm_service.settings, "project_path"):
                projects_dir = self.pm_service.settings.project_path
            else:
                projects_dir = "./projects"

            for channel_id in channel_ids:
                try:
                    channel_dir = os.path.join(projects_dir, str(channel_id))
                    video_ids_with_transcripts = set()

                    if os.path.exists(channel_dir) and os.path.isdir(channel_dir):
                        for video_dir in os.listdir(channel_dir):
                            video_path = os.path.join(channel_dir, video_dir)
                            if os.path.isdir(video_path):
                                transcript_file = os.path.join(video_path, f"{video_dir}_transcript.md")
                                if os.path.exists(transcript_file):
                                    video_ids_with_transcripts.add(video_dir)

                    transcript_info[str(channel_id)] = video_ids_with_transcripts

                except Exception as e:
                    logger.debug(f"Fehler beim Batch-Check für Channel {channel_id}: {e}")
                    transcript_info[str(channel_id)] = set()

        except Exception as e:
            logger.warning(f"Fehler beim Batch-Check der Transcript-Verzeichnisse: {e}")

        return transcript_info

    def _create_enriched_video_with_batch_info(self, transcript, transcript_info: dict) -> dict:
        """
        Erstellt ein erweitertes Transcript-Objekt mit Batch-Informationen.
        """
        try:
            video_id = str(transcript.video_id)
            # Hole Channel-ID aus der Relation
            channel_id = str(transcript.channel.channel_id) if transcript.channel else None

            # Verwende Datenbank-Status für konsistente Anzeige
            has_transcript = getattr(transcript, "is_transcribed", False)
            has_chapters = getattr(transcript, "has_chapters", False)

            # Optional: Dateipfad bestimmen falls benötigt
            transcript_path = None
            if has_transcript and channel_id:
                try:
                    # Hole Projektverzeichnis aus den Settings
                    if hasattr(self.pm_service, "settings") and hasattr(self.pm_service.settings, "project_path"):
                        projects_dir = self.pm_service.settings.project_path
                    else:
                        projects_dir = "./projects"
                    transcript_path = os.path.join(projects_dir, channel_id, video_id, f"{video_id}_transcript.md")
                except Exception:
                    pass  # Ignore path determination errors

            return {
                "transcript": transcript,
                "has_transcript": has_transcript,
                "has_chapters": has_chapters,
                "transcript_path": transcript_path,
            }

        except Exception as e:
            logger.warning(
                f"Fehler beim Erstellen der erweiterten Transcript-Info für {getattr(transcript, 'video_id', 'unknown')}: {e}"
            )
            # Fallback zu DB-Werten
            return {
                "transcript": transcript,
                "has_transcript": getattr(transcript, "is_transcribed", False),
                "has_chapters": getattr(transcript, "has_chapters", False),
                "transcript_path": None,
            }

    def _check_chapter_status_from_file(self, transcript_path: str) -> bool:
        """Überprüft, ob in einer Transkript-Datei Kapitel vorhanden sind."""
        try:
            if not transcript_path or not os.path.exists(transcript_path):
                return False

            with open(transcript_path, "r", encoding="utf-8") as f:
                content = f.read()
                return "## Kapitel" in content or "# Kapitel" in content or "chapters:" in content.lower()

        except Exception as e:
            logger.warning(f"Fehler beim Chapter-Check für Datei {transcript_path}: {e}")
            return False

    def _load_videos_sync(self):
        """Fallback: Synchrones Laden der Transcripts (alte Implementierung)."""
        logger.debug("DatabaseOverviewWidget: Fallback zu synchronem Transcript-Laden")
        self.model.removeRows(0, self.model.rowCount())
        try:
            # Lade Transcripts mit Channel-Relationen
            from yt_database.database import Channel

            transcripts = list(Transcript.select().join(Channel))
            for transcript in transcripts:
                # Erstelle erweiterte Transcript-Info für Kompatibilität
                enriched_video = {
                    "transcript": transcript,
                    "has_transcript": getattr(transcript, "is_transcribed", False),
                    "has_chapters": getattr(transcript, "has_chapters", False),
                    "transcript_path": None,
                }
                items = self._create_row_items_for_enriched_video(enriched_video)
                self.model.appendRow(items)
        except Exception as e:
            logger.error(f"Fehler beim synchronen Transcript-Laden: {e}")

    def _populate_table_with_videos(self, enriched_videos):
        """Füllt die Tabelle mit den geladenen Transcripts."""
        logger.debug(f"DatabaseOverviewWidget: Populiere Tabelle mit {len(enriched_videos)} Transcripts")

        try:
            # Blockiere Updates während der Population um Repaint-Probleme zu vermeiden
            self.table_view.setUpdatesEnabled(False)

            # Erst alle Zeilen entfernen
            self.model.removeRows(0, self.model.rowCount())

            # Transcripts in Batches hinzufügen für bessere Performance
            batch_size = 100  # Größere Batches da einfachere Verarbeitung
            total_videos = len(enriched_videos)

            for i in range(0, total_videos, batch_size):
                batch = enriched_videos[i : i + batch_size]
                batch_items = []

                # Sammle alle Items für diesen Batch
                for enriched_video in batch:
                    try:
                        items = self._create_row_items_for_enriched_video(enriched_video)
                        batch_items.append(items)
                    except Exception as e:
                        logger.warning(f"Fehler beim Erstellen der Tabellenzeile für Transcript: {e}")
                        continue

                # Füge Batch als Ganzes hinzu (effizienter)
                for items in batch_items:
                    self.model.appendRow(items)

                # Log Progress für große Batches
                if total_videos > 100:
                    logger.debug(
                        f"DatabaseOverviewWidget: Batch {i // batch_size + 1}/{(total_videos - 1) // batch_size + 1} verarbeitet"
                    )

            logger.debug(f"DatabaseOverviewWidget: Tabelle mit {self.model.rowCount()} Transcripts populiert")

        except Exception as e:
            logger.error(f"Kritischer Fehler beim Populieren der Tabelle: {e}")
            # Fallback: Versuche wenigstens einige Transcripts zu laden
            self._populate_table_fallback(enriched_videos[:100])
        finally:
            # Reaktiviere Updates
            self.table_view.setUpdatesEnabled(True)
            # Force einmaliges Update
            self.table_view.repaint()

    def _populate_table_fallback(self, enriched_videos):
        """Fallback-Methode für das Populieren der Tabelle bei Fehlern."""
        logger.debug("DatabaseOverviewWidget: Verwende Fallback-Methode für Tabellen-Population")
        try:
            self.model.removeRows(0, self.model.rowCount())
            for enriched_video in enriched_videos:
                try:
                    items = self._create_row_items_for_enriched_video(enriched_video)
                    self.model.appendRow(items)
                except Exception as e:
                    logger.debug(f"Fallback: Überspringe fehlerhaftes Transcript: {e}")
                    continue
            logger.debug(f"Fallback: {self.model.rowCount()} Transcripts geladen")
        except Exception as e:
            logger.error(f"Auch Fallback-Methode fehlgeschlagen: {e}")

    def _adjust_column_sizes(self):
        self.table_view.setColumnWidth(0, 300)  # Videotitel
        self.table_view.setColumnWidth(1, 120)  # Video-ID
        self.table_view.setColumnWidth(2, 100)  # Dauer
        self.table_view.setColumnWidth(3, 100)  # Kapitel (einfach)
        self.table_view.setColumnWidth(4, 100)  # Kapitel (detailliert)
        self.table_view.setColumnWidth(5, 100)  # Transkriptzeilen

    def filter_videos(self, text: str):
        """Filtert die Transcripts basierend auf dem Suchtext."""
        self.proxy_model.setFilterFixedString(text)

    def show_context_menu(self, position):
        index = self.table_view.indexAt(position)
        if not index.isValid():
            return

        # Hole alle selektierten Zeilen
        selected_indexes = self.table_view.selectionModel().selectedRows()
        selected_count = len(selected_indexes)

        # WICHTIG: Proxy-Model-Index zum Source-Model-Index mappen!
        source_index = self.proxy_model.mapToSource(index)
        row = source_index.row()

        # Daten der geklickten Zeile
        # Video-ID ist Spalte 1
        video_id = self.model.item(row, 1).text()
        # Transkribiert ist Spalte 7 - prüfen ob Icon gesetzt ist
        has_transcript = not self.model.item(row, 7).icon().isNull()
        # Spalte 5
        transcript_lines = int(self.model.item(row, 5).text()) if self.model.item(row, 5).text().isdigit() else 0
        # Video-URL ist Spalte 10
        youtube_url = self.model.item(row, 10).text()
        # Kanal-Handle ist Spalte 9
        channel_handle = self.model.item(row, 9).text() if self.model.item(row, 9) else ""
        # Für Kanal-Löschung: Versuche Channel-ID aus Transcript zu holen
        channel_id = ""
        channel_name = ""
        try:
            # Hole das Transcript-Objekt aus der DB für Channel-Info
            from yt_database.database import Channel

            transcripts = list(Transcript.select().join(Channel).where(Transcript.video_id == video_id))
            if transcripts:
                transcript = transcripts[0]
                if hasattr(transcript, "channel") and transcript.channel:
                    channel_id = str(transcript.channel.channel_id)
                    channel_name = str(transcript.channel.name)
        except Exception as e:
            logger.debug(f"Fehler beim Holen der Channel-Daten für Video {video_id}: {e}")

        menu = QMenu(self)

        # === SINGLE-SELECTION MENÜ ===
        if selected_count == 1:
            if video_id:
                open_file_action = menu.addAction(
                    Icons.get(":/icons/markdown-document-programming.svg"),
                    "Markdown-Datei öffnen",
                    lambda: self.file_open_requested.emit(video_id),
                )
                editor_action = menu.addAction(
                    Icons.get(":/icons/ai-edit-spark.svg"),
                    "Im Editor-Fenster öffnen",
                    lambda: self._open_in_editor_window(video_id),
                )
                download_action = menu.addAction(
                    Icons.get(":/icons/download-file.svg"),
                    "Transkript downloaden",
                    lambda: self.single_transcription_requested.emit(video_id, channel_handle, False),
                )
                menu.addSeparator()
                # Löschoptionen für einzelnes Video
                delete_video_action = menu.addAction(
                    Icons.get(":/icons/delete-1.svg"), "Video löschen", lambda: self._delete_video(video_id)
                )
                if channel_id and channel_name:
                    delete_channel_action = menu.addAction(
                        Icons.get(":/icons/delete-1.svg"),
                        f"Kanal '{channel_name}' löschen",
                        lambda: self._delete_channel(channel_id),
                    )

            if has_transcript and video_id:
                menu.addSeparator()
                chapter_action = menu.addAction(
                    Icons.get(":/icons/send_to_notebooklm.svg"),
                    "Starte Kapitelgenerierung",
                    lambda: self.chapter_generation_requested.emit(video_id),
                )
            if youtube_url.startswith("http") or youtube_url.startswith("https"):
                menu.addSeparator()
                youtube_action = menu.addAction(
                    Icons.get(":/icons/webcam-video.svg"),
                    "YouTube-Link öffnen",
                    lambda: QDesktopServices.openUrl(QUrl(youtube_url)),
                )

        # === MULTI-SELECTION MENÜ ===
        elif selected_count > 1:
            # Sammle alle Video-IDs der Selektion
            selected_video_ids = self._get_selected_video_ids(selected_indexes)
            not_transcribed_count = self._count_not_transcribed(selected_indexes)
            transcribed_count = selected_count - not_transcribed_count

            info_action = menu.addAction(Icons.get(Icons.INFO), f"Auswahl: {selected_count} Videos", None)
            info_action.setEnabled(False)  # Info-Header
            menu.addSeparator()

            if not_transcribed_count > 0:
                batch_download_action = menu.addAction(
                    Icons.get(Icons.DOWNLOAD),
                    f"Batch-Download ({not_transcribed_count} Videos)",
                    lambda: self._start_batch_transcription(selected_video_ids),
                )

            if transcribed_count > 0:
                batch_chapter_action = menu.addAction(
                    Icons.get(Icons.BOOK_OPEN),
                    f"Batch-Kapitelgenerierung ({transcribed_count} Videos)",
                    lambda: self._start_batch_chapter_generation(selected_video_ids),
                )

            menu.addSeparator()
            youtube_links_action = menu.addAction(
                Icons.get(Icons.VIDEO),
                "Alle YouTube-Links öffnen",
                lambda: self._open_all_youtube_links(selected_indexes),
            )

            # Batch-Löschoptionen
            menu.addSeparator()
            delete_multiple_action = menu.addAction(
                Icons.get(Icons.X_CIRCLE),
                f"{selected_count} Videos löschen",
                lambda: self._delete_multiple_videos(selected_video_ids),
            )

        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def _delete_video(self, video_id: str):
        """Löscht ein einzelnes Video nach Bestätigung."""
        try:
            # Hole Löschvorschau
            preview = self.pm_service.get_deletion_preview("video", video_id)

            # Zeige Bestätigungsdialog
            dialog = DeleteConfirmationDialog(delete_type="Video", preview_data=preview, parent=self)

            if dialog.exec():
                # Führe Löschung durch
                result = self.pm_service.delete_video_safe(video_id)

                if result["success"]:
                    QMessageBox.information(
                        self,
                        "Erfolgreich gelöscht",
                        f"Video wurde erfolgreich gelöscht.\n\n"
                        f"Gelöscht: 1 Video, "
                        f"{result.get('chapters_deleted', 0)} Kapitel",
                    )
                    # Aktualisiere die Anzeige
                    self.refresh_data()
                else:
                    QMessageBox.warning(
                        self, "Fehler beim Löschen", f"Fehler beim Löschen des Videos:\n{result['error']}"
                    )

        except Exception as e:
            logger.error(f"Fehler beim Löschen des Videos {video_id}: {e}")
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler beim Löschen:\n{str(e)}")

    def _delete_channel(self, channel_id: str):
        """Löscht einen kompletten Kanal nach Bestätigung."""
        try:
            # Hole Löschvorschau
            preview = self.pm_service.get_deletion_preview("channel", channel_id)

            # Zeige Bestätigungsdialog
            dialog = DeleteConfirmationDialog(delete_type="Kanal", preview_data=preview, parent=self)

            if dialog.exec():
                # Führe Löschung durch
                result = self.pm_service.delete_channel_safe(channel_id)

                if result["success"]:
                    QMessageBox.information(
                        self,
                        "Erfolgreich gelöscht",
                        f"Kanal wurde erfolgreich gelöscht.\n\n"
                        f"Gelöscht: {result.get('videos_deleted', 0)} Video(s), "
                        f"{result.get('chapters_deleted', 0)} Kapitel",
                    )
                    # Aktualisiere die Anzeige
                    self.refresh_data()
                else:
                    QMessageBox.warning(
                        self, "Fehler beim Löschen", f"Fehler beim Löschen des Kanals:\n{result['error']}"
                    )

        except Exception as e:
            logger.error(f"Fehler beim Löschen des Kanals {channel_id}: {e}")
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler beim Löschen:\n{str(e)}")

    def _delete_multiple_videos(self, video_ids: list):
        """Löscht mehrere Videos nach Bestätigung."""
        try:
            if not video_ids:
                return

            # Sammle Löschvorschau für alle Videos
            total_chapters = 0
            for video_id in video_ids:
                try:
                    preview = self.pm_service.get_deletion_preview("video", video_id)
                    if preview.get("success"):
                        total_chapters += preview.get("chapters_affected", 0)
                except Exception as e:
                    logger.warning(f"Fehler bei Löschvorschau für Video {video_id}: {e}")

            # Erstelle Batch-Statistik
            stats = {
                "success": True,
                "title": f"{len(video_ids)} Videos",
                "videos_affected": len(video_ids),
                "chapters_affected": total_chapters,
                "channels_affected": 0,
            }

            # Zeige Bestätigungsdialog
            dialog = DeleteConfirmationDialog(delete_type="Videos", preview_data=stats, parent=self)

            if dialog.exec():
                # Führe Batch-Löschung durch
                deleted_videos = 0
                deleted_chapters = 0
                errors = []

                for video_id in video_ids:
                    try:
                        result = self.pm_service.delete_video_safe(video_id)
                        if result["success"]:
                            deleted_videos += 1
                            deleted_chapters += result.get("chapters_deleted", 0)
                        else:
                            errors.append(f"Video {video_id}: {result['error']}")
                    except Exception as e:
                        errors.append(f"Video {video_id}: {str(e)}")

                if errors:
                    QMessageBox.warning(
                        self,
                        "Teilweise erfolgreich",
                        f"Batch-Löschung abgeschlossen mit Fehlern:\n\n"
                        f"Erfolgreich: {deleted_videos} Video(s), {deleted_chapters} Kapitel\n\n"
                        f"Fehler:\n"
                        + "\n".join(errors[:5])
                        + (f"\n... und {len(errors)-5} weitere" if len(errors) > 5 else ""),
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Erfolgreich gelöscht",
                        f"Batch-Löschung erfolgreich abgeschlossen.\n\n"
                        f"Gelöscht: {deleted_videos} Video(s), {deleted_chapters} Kapitel",
                    )

                # Aktualisiere die Anzeige
                self.refresh_data()

        except Exception as e:
            logger.error(f"Fehler beim Batch-Löschen: {e}")
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler beim Batch-Löschen:\n{str(e)}")

    def _open_in_editor_window(self, video_id: str) -> None:
        """Öffnet das Transkript zu einer Transcript-ID im separaten Editor-Fenster.
        Args:
            video_id (str): Die Transcript-ID aus der Datenbankübersicht.
        """
        from yt_database.gui.widgets.text_file_editor_widget import TextFileEditorWidget

        pm_service = self.pm_service

        file_path = pm_service.get_transcript_path_for_video_id(video_id)
        if not file_path:
            print(f"Transkriptdatei nicht gefunden für Transcript-ID: {video_id}")
            return
        editor = TextFileEditorWidget()
        editor.setWindowTitle(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            editor._content = content
            editor._file_path = file_path
            editor.text_edit.setPlainText(content)
        except Exception as e:
            print(f"Fehler beim Öffnen der Datei im Editor-Fenster: {e}")
        editor.show_as_window()

    def reload_videos_in_table(self) -> None:
        """Aktualisiert die Anzeige der Transcripts in der Tabelle."""
        logger.debug("DatabaseOverviewWidget: Lade Transcripts neu")
        self.refresh_data()

    # === MULTI-SELECTION HELPER METHODS ===

    def _get_selected_video_ids(self, selected_indexes) -> list[str]:
        """Extrahiert Video-IDs aus selektierten Tabellen-Zeilen."""
        video_ids = []
        for proxy_index in selected_indexes:
            source_index = self.proxy_model.mapToSource(proxy_index)
            row = source_index.row()
            video_id = self.model.item(row, 1).text()  # Video-ID ist Spalte 1
            if video_id:
                video_ids.append(video_id)
        return video_ids

    def _count_not_transcribed(self, selected_indexes) -> int:
        """Zählt nicht-transkribierte Videos in der Selektion."""
        count = 0
        for proxy_index in selected_indexes:
            source_index = self.proxy_model.mapToSource(proxy_index)
            row = source_index.row()
            has_transcript = (
                not self.model.item(row, 7).icon().isNull()
            )  # Transkribiert ist Spalte 7 - prüfen ob Icon gesetzt ist
            if not has_transcript:
                count += 1
        return count

    def _start_batch_transcription(self, video_ids: list[str]) -> None:
        """Startet Batch-Transcription für ausgewählte Videos."""
        logger.info(f"Database Widget: Starte Batch-Transcription für {len(video_ids)} Videos")
        self.batch_transcription_requested.emit(video_ids)

    def _start_batch_chapter_generation(self, video_ids: list[str]) -> None:
        """Startet Batch-Kapitelgenerierung für ausgewählte Videos."""
        logger.info(f"Database Widget: Starte Batch-Kapitelgenerierung für {len(video_ids)} Videos")
        # TODO: Signal für Batch-Chapter-Generation hinzufügen
        for video_id in video_ids:
            self.chapter_generation_requested.emit(video_id)

    def _open_all_youtube_links(self, selected_indexes) -> None:
        """Öffnet alle YouTube-Links der Selektion."""
        opened_count = 0
        for proxy_index in selected_indexes:
            source_index = self.proxy_model.mapToSource(proxy_index)
            row = source_index.row()
            youtube_url = self.model.item(row, 10).text()  # Video-URL ist Spalte 10
            if youtube_url and youtube_url.startswith("http"):
                QDesktopServices.openUrl(QUrl(youtube_url))
                opened_count += 1
        logger.info(f"Database Widget: {opened_count} YouTube-Links geöffnet")

    @Slot()
    def _on_transcript_download_finished(self):
        """Callback für Channel-Video-Worker-Finish."""
        logger.info("Channel-Video-Worker abgeschlossen.")
        self.progress_bar.setVisible(False)
        self.reload_videos_in_table()


class HyperlinkDelegate(QStyledItemDelegate):
    """Delegate für die Darstellung und Interaktion von Hyperlinks in einer Tabelle."""

    def paint(self, painter, option, index):
        url = index.data()
        if url and url.startswith("http"):
            painter.save()
            color = QColor(0, 102, 204)  # Blau
            font = option.font
            font.setUnderline(True)
            painter.setFont(font)
            painter.setPen(color)
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, url)
            painter.restore()
        else:
            super().paint(painter, option, index)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            url = index.data()
            if url and url.startswith("http"):
                QDesktopServices.openUrl(QUrl(url))
                return True
        return super().editorEvent(event, model, option, index)

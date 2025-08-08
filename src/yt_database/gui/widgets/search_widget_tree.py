"""
SearchWidgetTree für die hierarchische Volltextsuche in Kapiteln.

Dieses Widget stellt eine benutzerfreundliche Oberfläche für die Suche in Kapitel-Titeln
bereit und zeigt die Ergebnisse in einem hierarchischen TreeView an, gruppiert nach Videos.
"""

from collections import defaultdict
from typing import Dict, List

from loguru import logger
from PySide6.QtCore import Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from yt_database.gui.utils.icons import Icons
from yt_database.gui.widgets.delegates import RichTextHighlightDelegate
from yt_database.models.search_models import SearchResult
from yt_database.gui.utils.icons import Icons


class SearchWidgetTree(QWidget):
    """Ein Widget zur Suche in Kapiteln und zur hierarchischen Anzeige der Ergebnisse."""

    search_requested = Signal(str)

    def __init__(self, parent=None):
        """Initialisiert das Widget."""
        super().__init__(parent)
        # Setze einen Fenster-Titel, damit Tests, die windowTitle prüfen, bestehen.
        self.setWindowTitle("Erweiterte Suche")

        # Speichere Suchbegriffe für Hervorhebung
        self._current_search_terms = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Ruft die UI-Setup-Methoden in der richtigen Reihenfolge auf."""
        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self) -> None:
        """Initialisiert alle UI-Komponenten und konfiguriert ihre statischen Eigenschaften."""
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search_widget_tree_input")
        self.search_input.setPlaceholderText("Stichwort in Kapiteln suchen (z.B. 'Kritik', 'Politik', 'Analyse')...")
        self.search_input.setToolTip(
            "Gib einen oder mehrere Suchbegriffe ein. Treffer werden in den Kapiteln pro Video angezeigt."
        )

        self.search_button = QPushButton("Suchen")
        self.search_button.setObjectName("search_widget_tree_button")
        self.search_button.setToolTip("Startet die Suche nach den eingegebenen Begriffen (Enter möglich).")
        self.search_button.setIcon(Icons.get(Icons.SEARCH))

        self.results_tree = QTreeView()
        self.results_tree.setObjectName("search_widget_tree_results")
        self.results_tree.setToolTip("Hier werden die Suchergebnisse als Baum angezeigt: Video → Sektion → Kapitel.")
        self.results_model = QStandardItemModel(self)
        self.results_tree.setModel(self.results_model)

        # Konfiguration der TreeView (ursprünglich in _setup_tree)
        self.results_model.setHorizontalHeaderLabels(["Video / Kapitel", "Kanal", "Zeitstempel"])
        header = self.results_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.resizeSection(0, 300)  # Mindestbreite Video/Kapitel
        header.resizeSection(1, 150)  # Mindestbreite Kanal
        self.results_tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_tree.setSortingEnabled(True)
        self.results_tree.setAlternatingRowColors(True)

        # Delegate für Wort-Hervorhebung einsetzen (Spalten 0 und 1)
        self._highlight_delegate = RichTextHighlightDelegate(lambda: self._current_search_terms)
        self.results_tree.setItemDelegateForColumn(0, self._highlight_delegate)
        self.results_tree.setItemDelegateForColumn(1, self._highlight_delegate)

        self.status_label = QLabel("Bitte gib einen Suchbegriff ein.")
        self.status_label.setObjectName("search_widget_tree_status_label")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setToolTip("Status- und Hinweistexte zur Suche werden hier angezeigt.")
        self.status_label.hide()

    def _setup_layouts(self) -> None:
        """Ordnet die initialisierten Widgets in Layouts an."""
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.results_tree)
        self.setLayout(main_layout)

    def _setup_signals(self) -> None:
        """Verbindet die Signale der permanenten Widgets mit ihren Slots."""
        self.search_button.clicked.connect(self._on_search_clicked)
        self.search_input.returnPressed.connect(self._on_search_clicked)
        self.results_tree.doubleClicked.connect(self._on_result_double_clicked)

    def set_search_terms(self, search_terms: List[str]):
        """Setzt die aktuellen Suchbegriffe für die Hervorhebung."""
        self._current_search_terms = search_terms if search_terms else []
        logger.debug(f"SearchWidgetTree: Suchbegriffe für Hervorhebung gesetzt: {self._current_search_terms}")
        self._refresh_highlighting()

    def _highlight_search_terms(self, text: str) -> str:
        """Hebt Suchbegriffe im Text farblich hervor - verwendet Rich Text für Qt."""
        if not self._current_search_terms or not text:
            return text

        highlighted_text = text

        # Sortiere Suchbegriffe nach Länge (längste zuerst) um Überschneidungen zu vermeiden
        sorted_terms = sorted(self._current_search_terms, key=len, reverse=True)

        for term in sorted_terms:
            if term.strip():  # Nur nicht-leere Begriffe
                # Case-insensitive Suche mit Rich Text Hervorhebung für Qt
                import re

                pattern = re.compile(re.escape(term), re.IGNORECASE)
                highlighted_text = pattern.sub(
                    lambda match: f'<span style="background-color: #FFFF00; color: #000000; font-weight: bold;">{match.group()}</span>',
                    highlighted_text,
                )

        return highlighted_text

    def _create_highlighted_item(self, text: str, prefix: str = "") -> QStandardItem:
        """Erstellt ein QStandardItem mit farblicher Hervorhebung."""

        full_text = f"{prefix}{text}"
        item = QStandardItem(full_text)
        item.setEditable(False)

        # Optional: Tooltip setzen, wenn ein Begriff vorkommt
        if self._current_search_terms and any(
            t.strip() and t.lower() in text.lower() for t in self._current_search_terms
        ):
            item.setToolTip(f"Suchbegriff gefunden: {text}")

        return item

    def _refresh_highlighting(self) -> None:
        """Erzwingt ein Redraw aller sichtbaren Zellen, damit der Delegate neu zeichnet."""
        if not self.results_model or self.results_model.rowCount() == 0:
            self.results_tree.viewport().update()
            return
        top_left = self.results_model.index(0, 0)
        bottom_right = self.results_model.index(
            max(0, self.results_model.rowCount() - 1), max(0, self.results_model.columnCount() - 1)
        )
        self.results_model.dataChanged.emit(top_left, bottom_right)
        self.results_tree.viewport().update()

    @Slot()
    def _on_search_clicked(self) -> None:
        """Wird ausgelöst, wenn die Suche gestartet wird."""
        keyword = self.search_input.text().strip()
        if keyword:
            logger.debug(f"Benutzer startet Suche nach: '{keyword}'")

            # Extrahiere und speichere Suchbegriffe für Hervorhebung
            search_terms = [term.strip() for term in keyword.split() if term.strip()]
            self.set_search_terms(search_terms)

            # UI für den Ladezustand vorbereiten
            self.results_model.removeRows(0, self.results_model.rowCount())
            self.status_label.setText("Suche läuft...")
            self.status_label.show()
            self.results_tree.hide()
            # Signal senden, um die eigentliche Suche im Backend auszulösen
            self.search_requested.emit(keyword)

    @Slot(list)
    def display_results(self, results: List[SearchResult]) -> None:
        """Slot zum Anzeigen der Suchergebnisse in der TreeView."""
        logger.debug(f"Zeige {len(results)} Suchergebnisse hierarchisch an.")
        self.results_model.removeRows(0, self.results_model.rowCount())
        # Wichtig: Header neu setzen, da removeRows sie löschen kann
        self.results_model.setHorizontalHeaderLabels(["Video / Kapitel", "Kanal", "Zeitstempel"])

        if not results:
            self.status_label.setText("Keine Ergebnisse für deine Suche gefunden.")
            self.status_label.show()
            self.results_tree.hide()
            return

        self.status_label.hide()
        self.results_tree.show()

        # Schritt 1: Ergebnisse nach Video gruppieren
        videos: Dict[str, List[SearchResult]] = defaultdict(list)
        for res in results:
            videos[res.video_title].append(res)

        # Schritt 2: Baumstruktur aufbauen
        for video_title, chapters in videos.items():
            # Hole Kanalinformationen vom ersten Kapitel (alle haben den gleichen Kanal)
            first_chapter = chapters[0]
            channel_display = first_chapter.channel_name
            if first_chapter.channel_handle:
                channel_display = f"{first_chapter.channel_name} ({first_chapter.channel_handle})"

            # Top-Level-Item für das Video erstellen
            video_item = self._create_highlighted_item(video_title, "")
            video_item.setData(None, Qt.ItemDataRole.UserRole)  # Kein Link für Video-Item
            video_item.setIcon(Icons.get(Icons.VIDEO))

            channel_item = QStandardItem(channel_display)
            channel_item.setEditable(False)
            channel_item.setData(None, Qt.ItemDataRole.UserRole)

            chapter_count_item = QStandardItem(f"{len(chapters)} Treffer")
            chapter_count_item.setEditable(False)
            chapter_count_item.setData(None, Qt.ItemDataRole.UserRole)

            self.results_model.appendRow([video_item, channel_item, chapter_count_item])

            # Child-Items für jedes gefundene Kapitel direkt unter dem Video-Item erstellen
            for chapter in chapters:
                chapter_item = self._create_highlighted_item(chapter.chapter_title, "")
                chapter_item.setIcon(Icons.get(Icons.BOOK_OPEN))
                # Link im Item speichern
                chapter_item.setData(chapter.timestamp_url, Qt.ItemDataRole.UserRole)

                channel_child = QStandardItem("")
                channel_child.setEditable(False)
                channel_child.setData(chapter.timestamp_url, Qt.ItemDataRole.UserRole)

                timestamp_item = QStandardItem(chapter.start_time_str)
                timestamp_item.setEditable(False)
                timestamp_item.setData(chapter.timestamp_url, Qt.ItemDataRole.UserRole)

                video_item.appendRow([chapter_item, channel_child, timestamp_item])

        # Performance-Optimierung: Nur bei wenigen Videos automatisch expandieren
        if len(videos) <= 3:
            self.results_tree.expandAll()
        else:
            logger.debug(f"Viele Ergebnisse ({len(videos)} Videos) - TreeView nicht automatisch expandiert")

        self.results_tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    @Slot()
    def _on_result_double_clicked(self, index) -> None:
        """Öffnet den YouTube-Link beim Doppelklick auf eine Zeile."""
        # Hole das geklickte Item aus dem Model
        item = self.results_model.itemFromIndex(index)
        if not item:
            return

        # Hole den im Item gespeicherten Link (UserRole)
        url_str = item.data(Qt.ItemDataRole.UserRole)

        if url_str:
            logger.info(f"Öffne YouTube-Link: {url_str}")
            QDesktopServices.openUrl(QUrl(url_str))
        else:
            logger.debug("Doppelklick auf Video-Item (kein Link verfügbar)")

    def _extract_video_id_from_url(self, timestamp_url: str) -> str:
        """Extrahiert die Video-ID aus einer YouTube-URL."""
        try:
            import re

            # Regex für YouTube URLs: youtube.com/watch?v=VIDEO_ID oder youtu.be/VIDEO_ID
            patterns = [
                r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
                r"youtu\.be/([a-zA-Z0-9_-]+)",
                r"youtube\.com/embed/([a-zA-Z0-9_-]+)",
            ]

            for pattern in patterns:
                match = re.search(pattern, timestamp_url)
                if match:
                    return match.group(1)

            return ""
        except Exception as e:
            logger.warning(f"Fehler beim Extrahieren der Video-ID aus URL {timestamp_url}: {e}")
            return ""

    def _get_all_chapters_for_video(self, video_id: str) -> List:
        """Holt alle Kapitel für ein Video aus der Datenbank."""
        try:
            from yt_database.database import Chapter, Transcript

            chapters = list(
                Chapter.select().join(Transcript).where(Transcript.video_id == video_id).order_by(Chapter.start_seconds)
            )
            return chapters
        except Exception as e:
            logger.warning(f"Fehler beim Laden der Kapitel für Video {video_id}: {e}")
            return []

    def _format_seconds_to_time(self, seconds: int) -> str:
        """Formatiert Sekunden zu einer lesbaren Zeitangabe."""
        try:
            hours, remainder = divmod(seconds, 3600)
            minutes, secs = divmod(remainder, 60)

            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes:02d}:{secs:02d}"
        except Exception:
            return f"{seconds}s"

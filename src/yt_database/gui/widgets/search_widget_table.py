"""
SearchWidget für die Volltextsuche in Kapiteln mit hierarchischer und tabellarischer Ansicht.

Dieses Widget kombiniert ein TreeView (oben) für hierarchische Suchergebnisse mit einem
TableView (unten) für detaillierte Zeitstempel-Anzeige des ausgewählten Videos.
"""

from typing import List

from loguru import logger
from PySide6.QtCore import Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from yt_database.gui.utils.icons import Icons
from yt_database.gui.widgets.delegates import RichTextHighlightDelegate
from yt_database.gui.widgets.search_widget_tree import SearchWidgetTree
from yt_database.models.search_models import SearchResult


class SearchWidget(QWidget):
    """Ein Widget zur Suche in Kapiteln und zur Anzeige der Ergebnisse."""

    search_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Database - Erweiterte Suche")
        self.setMinimumSize(1000, 700)

        # Status-Tracking
        self._is_search_running = False
        self._current_search_terms = []  # Speichert die aktuellen Suchbegriffe für Hervorhebung

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()
        self._setup_table()

        logger.debug("SearchWidget initialisiert")

    def _setup_widgets(self):
        """Erstellt und konfiguriert alle UI-Komponenten."""
        # TreeView Widget für hierarchische Suchergebnisse
        self.tree_widget = SearchWidgetTree()
        self.tree_widget.setMinimumHeight(400)  # Mindesthöhe für TreeView
        self.tree_widget.setToolTip(
            "Hierarchische Suchergebnisse: Wähle ein Video aus, um alle seine Zeitstempel unten zu sehen."
        )

        self.tree_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # TableView für alle Zeitstempel des ausgewählten Videos
        self.results_table = QTableView()
        self.results_table.setObjectName("search_widget_results_table")
        self.results_table.setToolTip(
            "Detaillierte Zeitstempel-Liste des oben ausgewählten Videos. Doppelklick öffnet YouTube-Link."
        )
        self.results_model = QStandardItemModel(self)
        self.results_table.setModel(self.results_model)

        # Label für TableView Status
        self.table_status_label = QLabel("Wählen Sie ein Video im oberen Bereich aus, um alle Zeitstempel zu sehen.")
        self.table_status_label.setObjectName("search_widget_table_status_label")
        self.table_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_status_label.setStyleSheet("font-style: italic; color: gray; padding: 10px;")
        self.table_status_label.setToolTip("Hinweistext für die Tabellen-Ansicht.")

        # Splitter für vertikale Aufteilung
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setToolTip("Ziehe am Griff, um die Größenverhältnisse zwischen Baum und Tabelle anzupassen.")

        # Stelle sicher, dass TreeView genügend Platz bekommt
        # (Mindesthöhe wurde bereits oben bei _setup_widgets gesetzt)

        self.splitter.addWidget(self.tree_widget)

        # Container für TableView mit Label
        table_container = QWidget()
        table_container.setMinimumHeight(200)
        table_layout = QVBoxLayout(table_container)
        table_layout.addWidget(QLabel("Alle Zeitstempel des ausgewählten Videos:"))
        table_layout.addWidget(self.table_status_label)
        table_layout.addWidget(self.results_table)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter.addWidget(table_container)

        # Setze Splitter-Eigenschaften für bessere Größenverteilung
        self.splitter.setStretchFactor(0, 3)  # TreeView bekommt 3/4 des Platzes
        self.splitter.setStretchFactor(1, 1)  # TableView bekommt 1/4 des Platzes

        # Setze explizite Anfangsgrößen (TreeView größer als TableView)
        self.splitter.setSizes([500, 200])  # TreeView: 500px, TableView: 200px
        self.splitter.setHandleWidth(8)  # Sichtbarer Griff zum Ziehen

        # Setze Splitter-Verhältnis explizit nach dem Setup
        # Verwende QTimer um sicherzustellen, dass der Splitter vollständig initialisiert ist
        from PySide6.QtCore import QTimer

        QTimer.singleShot(100, lambda: self.splitter.setSizes([400, 300]))

    def _setup_layouts(self):
        """Ordnet die UI-Komponenten in Layouts an."""
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.splitter)

    def _setup_signals(self):
        """Verbindet die Signale der UI-Elemente mit den Slots."""
        # Verbinde TreeWidget Signale weiter
        self.tree_widget.search_requested.connect(self._on_search_requested)

        # Verbinde TreeView Selection mit TableView Update
        self.tree_widget.results_tree.clicked.connect(self._on_tree_item_clicked)

        # TableView Doppelklick für YouTube Links
        self.results_table.doubleClicked.connect(self._on_result_double_clicked)

    @Slot(str)
    def _on_search_requested(self, search_query: str):
        """Behandelt Suchanfragen und extrahiert Suchbegriffe für Hervorhebung."""
        # Extrahiere Suchbegriffe aus der Suchanfrage (einfache Worttrennung)
        search_terms = [term.strip() for term in search_query.split() if term.strip()]
        self.set_search_terms(search_terms)

        # Leite Suchbegriffe auch an das TreeWidget weiter
        self.tree_widget.set_search_terms(search_terms)

        # Leite Signal weiter
        self.search_requested.emit(search_query)

    def _setup_table(self):
        """Konfiguriert die Ergebnistabelle."""
        self.results_model.setHorizontalHeaderLabels(["Kapitel-Titel", "Zeitstempel", "YouTube-Link"])
        header = self.results_table.horizontalHeader()
        # Benutzer-resizable Spalten
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Kapitel-Spalte
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Zeit-Spalte
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Link-Spalte
        header.setStretchLastSection(False)
        # Startbreiten
        header.resizeSection(0, 600)
        header.resizeSection(1, 120)
        header.resizeSection(2, 260)

        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setSortingEnabled(True)
        self.results_table.setAlternatingRowColors(True)

        # Delegate für Wort-Hervorhebung in der Titelspalte
        self._table_highlight_delegate = RichTextHighlightDelegate(lambda: self._current_search_terms)
        self.results_table.setItemDelegateForColumn(0, self._table_highlight_delegate)

    @Slot()
    def _on_tree_item_clicked(self, index):
        """Wird aufgerufen, wenn ein Item im TreeView angeklickt wird."""
        try:
            logger.debug(f"TreeView Item angeklickt: {index}")

            if not index.isValid():
                logger.debug("Ungültiger Index")
                return

            # Hole das Model Item (wir wissen, dass es ein QStandardItemModel ist)
            model = self.tree_widget.results_tree.model()
            if not isinstance(model, QStandardItemModel):
                logger.debug("Kein QStandardItemModel gefunden")
                return

            item = model.itemFromIndex(index)
            if not item:
                logger.debug("Kein Item für Index gefunden")
                return

            logger.debug(f"Item Text: {item.text()}")

            # Extrahiere Video-ID vom angeklickten Item
            video_id = self._extract_video_id_from_model_item(item)
            logger.debug(f"Extrahierte Video-ID: {video_id}")

            if video_id:
                # Lade alle Zeitstempel für dieses Video
                self._load_all_timestamps_for_video(video_id)
            else:
                logger.debug("Keine Video-ID gefunden - TableView wird nicht aktualisiert")

        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten des TreeView-Klicks: {e}")

    def _extract_video_id_from_tree_selection(self, index) -> str:
        """Extrahiert die Video-ID aus der TreeView-Auswahl."""
        try:
            # Navigiere durch die Hierarchie, um eine URL zu finden
            model = self.tree_widget.results_model

            # Wenn es ein Video-Item ist, schaue nach einem Child mit URL
            item = model.itemFromIndex(index)
            if item:
                # Durchsuche alle Kinder nach URLs
                for row in range(item.rowCount()):
                    child = item.child(row, 0)
                    if child:
                        url = child.data(Qt.ItemDataRole.UserRole)
                        if url:
                            return self._extract_video_id_from_url(url)

                        # Rekursiv in weitere Kinder schauen
                        for subrow in range(child.rowCount()):
                            subchild = child.child(subrow, 0)
                            if subchild:
                                suburl = subchild.data(Qt.ItemDataRole.UserRole)
                                if suburl:
                                    return self._extract_video_id_from_url(suburl)

                # Falls das Item selbst eine URL hat
                url = item.data(Qt.ItemDataRole.UserRole)
                if url:
                    return self._extract_video_id_from_url(url)

            return ""
        except Exception as e:
            logger.warning(f"Fehler beim Extrahieren der Video-ID: {e}")
            return ""

    def _extract_video_id_from_model_item(self, item: QStandardItem) -> str:
        """Extrahiert die Video-ID aus einem Model-Item."""
        try:
            # Zuerst schauen wir, ob das Item selbst eine URL hat
            url = item.data(Qt.ItemDataRole.UserRole)
            if url and isinstance(url, str):
                video_id = self._extract_video_id_from_url(url)
                if video_id:
                    logger.debug(f"Video-ID aus Item selbst extrahiert: {video_id}")
                    return video_id

            # Wenn das Item keine URL hat, schauen wir in die Children
            # Traverse alle Children auf der ersten Ebene
            for row in range(item.rowCount()):
                child = item.child(row, 0)
                if child:
                    child_url = child.data(Qt.ItemDataRole.UserRole)
                    if child_url and isinstance(child_url, str):
                        video_id = self._extract_video_id_from_url(child_url)
                        if video_id:
                            logger.debug(f"Video-ID aus Child-Item extrahiert: {video_id}")
                            return video_id

                    # Traverse auch Sub-Children (zweite Ebene)
                    for subrow in range(child.rowCount()):
                        subchild = child.child(subrow, 0)
                        if subchild:
                            subchild_url = subchild.data(Qt.ItemDataRole.UserRole)
                            if subchild_url and isinstance(subchild_url, str):
                                video_id = self._extract_video_id_from_url(subchild_url)
                                if video_id:
                                    logger.debug(f"Video-ID aus Sub-Child-Item extrahiert: {video_id}")
                                    return video_id

            # Falls wir ein Child-Item geklickt haben, schauen wir nach oben zum Parent
            parent_item = item.parent()
            if parent_item:
                # Durchsuche alle Siblings des Parent nach URLs
                for row in range(parent_item.rowCount()):
                    sibling = parent_item.child(row, 0)
                    if sibling:
                        for subrow in range(sibling.rowCount()):
                            subsibling = sibling.child(subrow, 0)
                            if subsibling:
                                subsibling_url = subsibling.data(Qt.ItemDataRole.UserRole)
                                if subsibling_url and isinstance(subsibling_url, str):
                                    video_id = self._extract_video_id_from_url(subsibling_url)
                                    if video_id:
                                        logger.debug(f"Video-ID aus Parent-Sibling extrahiert: {video_id}")
                                        return video_id

            logger.debug(f"Keine Video-ID gefunden für Item: {item.text()}")
            return ""
        except Exception as e:
            logger.warning(f"Fehler beim Extrahieren der Video-ID aus Model-Item: {e}")
            return ""

    def _extract_video_id_from_url(self, timestamp_url: str) -> str:
        """Extrahiert die Video-ID aus einer YouTube-URL."""
        try:
            import re

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

    def _load_all_timestamps_for_video(self, video_id: str):
        """Lädt alle Zeitstempel für ein Video und zeigt sie in der Tabelle an."""
        try:
            from yt_database.database import Chapter, Transcript

            # Hole alle Kapitel des Videos
            chapters = list(
                Chapter.select().join(Transcript).where(Transcript.video_id == video_id).order_by(Chapter.start_seconds)
            )

            # Leere die Tabelle
            self.results_model.removeRows(0, self.results_model.rowCount())

            if not chapters:
                self.table_status_label.setText("Keine Zeitstempel für dieses Video gefunden.")
                self.table_status_label.show()
                self.results_table.hide()
                return

            self.table_status_label.hide()
            self.results_table.show()

            # Fülle die Tabelle mit allen Kapiteln
            for chapter in chapters:
                # Formatiere Zeitstempel
                time_str = self._format_seconds_to_time(chapter.start_seconds)

                # Erstelle YouTube-URL
                youtube_url = f"https://youtube.com/watch?v={video_id}&t={chapter.start_seconds}s"

                # Wende Hervorhebung auf Titel an und erstelle Items
                title_item = self._create_highlighted_item(chapter.title)
                title_item.setIcon(Icons.get(Icons.BOOK_OPEN))  # Icon für Kapitel

                time_item = QStandardItem(time_str)
                time_item.setIcon(Icons.get(Icons.PLAY))  # Icon für Zeitstempel

                url_item = QStandardItem(youtube_url)
                url_item.setIcon(Icons.get(Icons.VIDEO))  # Icon für YouTube-Link

                row = [title_item, time_item, url_item]

                # Speichere URL für Doppelklick
                for item in row:
                    item.setData(youtube_url, Qt.ItemDataRole.UserRole)

                self.results_model.appendRow(row)

            logger.debug(f"Zeige {len(chapters)} Zeitstempel für Video {video_id} an")

        except Exception as e:
            logger.error(f"Fehler beim Laden der Zeitstempel für Video {video_id}: {e}")
            self.table_status_label.setText("Fehler beim Laden der Zeitstempel.")
            self.table_status_label.show()
            self.results_table.hide()

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

    def _create_highlighted_item(self, text: str) -> QStandardItem:
        """Erstellt ein QStandardItem mit farblicher Hervorhebung."""
        item = QStandardItem(text)
        item.setEditable(False)

        # Optional: Tooltip, wenn Suchbegriff vorkommt
        if self._current_search_terms and any(
            t.strip() and t.lower() in text.lower() for t in self._current_search_terms
        ):
            item.setToolTip(f"Suchbegriff gefunden: {text}")

        return item

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

    def set_search_terms(self, search_terms: List[str]):
        """Setzt die aktuellen Suchbegriffe für die Hervorhebung."""
        self._current_search_terms = search_terms if search_terms else []
        logger.debug(f"SearchWidget: Suchbegriffe für Hervorhebung gesetzt: {self._current_search_terms}")
        # Refresh Table-Rendering
        if self.results_model is not None and self.results_model.rowCount() > 0:
            top_left = self.results_model.index(0, 0)
            bottom_right = self.results_model.index(
                max(0, self.results_model.rowCount() - 1), max(0, self.results_model.columnCount() - 1)
            )
            self.results_model.dataChanged.emit(top_left, bottom_right)
            self.results_table.viewport().update()

    @Slot(list)
    def display_results(self, results: List[SearchResult]):
        """Slot zum Weiterleiten der Suchergebnisse an das TreeWidget."""
        self.tree_widget.display_results(results)

        # Leere die Tabelle und zeige Hinweis
        self.results_model.removeRows(0, self.results_model.rowCount())
        self.table_status_label.setText("Wählen Sie ein Video im oberen Bereich aus, um alle Zeitstempel zu sehen.")
        self.table_status_label.show()
        self.results_table.hide()

    @Slot()
    def _on_result_double_clicked(self, index):
        """Öffnet den YouTube-Link beim Doppelklick auf eine Zeile."""
        item = self.results_model.itemFromIndex(index)
        if not item:
            return

        url_str = item.data(Qt.ItemDataRole.UserRole)
        if url_str:
            logger.info(f"Öffne YouTube-Link: {url_str}")
            QDesktopServices.openUrl(QUrl(url_str))

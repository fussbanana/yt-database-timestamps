from typing import List

from loguru import logger
from PySide6.QtCore import QEvent, QSortFilterProxyModel, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QColor, QDesktopServices, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from yt_database.gui.utils.icons import Icons
from yt_database.models.models import TranscriptData
from yt_database.services.analysis_prompt_service import AnalysisPromptService, PromptType


class VideoSelectionTableWidget(QWidget):
    video_selection_changed = Signal(list)
    file_open_requested = Signal(str)
    chapter_generation_requested = Signal(str)
    prompt_text_changed = Signal(str, str)
    text_editor_open_requested = Signal(str)

    def __init__(self, project_manager_service, parent=None):
        super().__init__(parent)
        self.project_manager_service = project_manager_service
        self.analysis_prompt_service = AnalysisPromptService()
        self._all_videos = []
        self._setup_ui()
        self._setup_columns()

    # --------------------
    # UI-Setup
    # --------------------
    def _setup_ui(self):
        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self):
        from yt_database.config.settings import settings

        # Models
        self.model = QStandardItemModel(0, 0, self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(-1)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setObjectName("video_selection_search_input")
        self.search_input.setPlaceholderText("Filtere nach Titel oder Transcript-ID...")
        self.search_input.setToolTip(
            "Filtert die angezeigten Videos nach Titel, Kanal oder Transcript-ID.\nGeben Sie Suchbegriffe ein, um die Liste zu durchsuchen."
        )

        # Prompt Combo
        self.prompt_combo = QComboBox()
        self.prompt_combo.setObjectName("video_selection_prompt_combo")
        self.prompt_combo.setToolTip(
            "Wählen Sie den Typ der Kapitel aus, die für die ausgewählten Videos generiert werden sollen.\nVerschiedene Prompt-Typen erzeugen unterschiedliche Kapitel-Strukturen."
        )
        current_prompt_type = None
        for prompt_type in self.analysis_prompt_service.get_available_prompt_types():
            description = self.analysis_prompt_service.get_prompt_description(prompt_type)
            self.prompt_combo.addItem(description, prompt_type)
            if prompt_type.value == settings.prompt_type:
                current_prompt_type = prompt_type
        if current_prompt_type:
            index = self.prompt_combo.findData(current_prompt_type)
            if index >= 0:
                self.prompt_combo.setCurrentIndex(index)

        # Table
        self.table_view = QTableView()
        self.table_view.setObjectName("video_selection_table_view")
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.CurrentChanged)
        self.table_view.setSortingEnabled(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setModel(self.proxy_model)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.setToolTip(
            "Tabelle mit verfügbaren Videos für die Transkription oder Kapitelgenerierung.\nMarkieren Sie Videos durch Anklicken der Checkboxen.\nRechtsklick für weitere Optionen."
        )

        # Button
        self.load_videos_button = QPushButton("Transcripts aus Datenbank laden")
        self.load_videos_button.setObjectName("video_selection_load_videos_button")
        self.load_videos_button.setToolTip(
            "Lädt alle Videos aus der Datenbank, die noch keine vollständigen Transkripte oder Kapitel haben.\nNützlich um Videos zu finden, die noch bearbeitet werden müssen."
        )

    def _setup_layouts(self):
        prompt_layout = QHBoxLayout()
        prompt_layout.addWidget(QLabel("Kapitel-Typ:"))
        prompt_layout.addWidget(self.prompt_combo)
        prompt_layout.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(prompt_layout)
        layout.addWidget(self.search_input)
        layout.addWidget(self.table_view)
        layout.addWidget(self.load_videos_button)
        self.setLayout(layout)

    def _setup_signals(self):
        self.search_input.textChanged.connect(self.proxy_model.setFilterFixedString)
        self.prompt_combo.currentIndexChanged.connect(self._on_prompt_text_changed)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)
        self.model.itemChanged.connect(self._on_item_changed)
        self.load_videos_button.clicked.connect(self._on_load_videos_clicked)

        # Zusätzliche Verbindung für bessere Reaktion auf Auswahländerungen
        self.model.dataChanged.connect(self._on_data_changed)

    # --------------------
    # Tabellen-Setup
    # --------------------
    def _setup_columns(self):
        self.model.setHorizontalHeaderLabels(["", "Titel", "Transcript-ID", "Status", "Transcript-URL"])
        self.table_view.setItemDelegateForColumn(4, HyperlinkDelegate(self.table_view))

    # --------------------
    # Public API
    # --------------------
    def get_selected_prompt_type(self) -> PromptType:
        return self.prompt_combo.currentData()

    def get_selected_prompt_text(self) -> str:
        prompt_type = self.get_selected_prompt_type()
        return self.analysis_prompt_service.get_prompt(prompt_type)

    def get_prompt_description(self, prompt_type: PromptType) -> str:
        return self.analysis_prompt_service.get_prompt_description(prompt_type)

    def get_selected_video_ids(self) -> list:
        selected_ids = []
        for row in range(self.model.rowCount()):
            checkbox_item = self.model.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                id_item = self.model.item(row, 2)
                selected_ids.append(id_item.text())
        return selected_ids

    def set_videos(self, transcripts: List[TranscriptData]) -> None:
        self._all_videos = transcripts
        self.model.setRowCount(0)
        for transcript in transcripts:
            items = self._create_row_items_for_video(transcript)
            self.model.appendRow(items)
        self.table_view.resizeColumnsToContents()
        self._adjust_column_sizes()

    def set_videos_from_json(self, json_path: str) -> None:
        from yt_database.utils.json_parsing import parse_channel_videos_json

        transcripts = parse_channel_videos_json(json_path)
        self.set_videos(transcripts)

    # --------------------
    # Event-Handler
    # --------------------
    def _on_load_videos_clicked(self) -> None:
        transcripts = self.project_manager_service.get_videos_without_transcript_or_chapters()
        transcript_data_list = self.project_manager_service.videos_to_transcript_data(transcripts)
        self.set_videos(transcript_data_list)

    def _on_item_changed(self, item: QStandardItem):
        if item.column() == 0:
            selected_ids = self.get_selected_video_ids()
            logger.debug(f"VideoSelectionTable: Item changed, ausgewählte IDs: {len(selected_ids)}")
            self.video_selection_changed.emit(selected_ids)

    def _on_data_changed(self, top_left, bottom_right, roles):
        """Reagiert auf Datenänderungen im Model, insbesondere Checkbox-Änderungen."""
        # Prüfen ob sich Checkboxen in der ersten Spalte geändert haben
        if top_left.column() <= 0 <= bottom_right.column():
            selected_ids = self.get_selected_video_ids()
            logger.debug(f"VideoSelectionTable: Data changed, ausgewählte IDs: {len(selected_ids)}")
            self.video_selection_changed.emit(selected_ids)

    def _on_prompt_text_changed(self, index: int) -> None:
        from yt_database.config.settings import settings

        selected_prompt_type = self.prompt_combo.itemData(index)
        if selected_prompt_type:
            prompt_description = self.get_prompt_description(selected_prompt_type)
            logger.debug(f"Prompt-Typ geändert zu: {selected_prompt_type.value}")
            settings.prompt_type = selected_prompt_type.value
            settings.save_to_yaml()
            self.prompt_text_changed.emit(selected_prompt_type.value, prompt_description)

    # --------------------
    # Hilfsmethoden
    # --------------------
    def _create_row_items_for_video(self, transcript: TranscriptData) -> list:
        checkbox_item = QStandardItem()
        checkbox_item.setCheckable(True)
        checkbox_item.setEditable(True)

        title_item = QStandardItem(f"{transcript.title} ({transcript.channel_name})")
        title_item.setEditable(False)

        id_item = QStandardItem(str(transcript.video_id))
        id_item.setEditable(False)

        has_transcript = bool(transcript.entries)
        has_chapters = bool(transcript.chapters)
        has_error = bool(transcript.error_reason)

        if has_error:
            status_text = f"Fehler: {transcript.error_reason}"
            status_icon = Icons.get(Icons.X_CIRCLE)
            is_completed = True
        elif has_transcript and has_chapters:
            status_text = "Vollständig (Transkript + Kapitel)"
            status_icon = Icons.get(Icons.CHECK_CIRCLE)
            is_completed = True
        elif has_transcript:
            status_text = "Nur Transkript"
            status_icon = Icons.get(Icons.FILE_TEXT)
            is_completed = True
        elif has_chapters:
            status_text = "Nur Kapitel"
            status_icon = Icons.get(Icons.BOOK)
            is_completed = True
        else:
            status_text = "Offen"
            status_icon = Icons.get(Icons.HOURGLASS)
            is_completed = False

        status_item = QStandardItem(status_text)
        status_item.setEditable(False)
        status_item.setIcon(status_icon)

        url_item = QStandardItem(str(transcript.video_url) if getattr(transcript, "video_url", None) else "")
        url_item.setEditable(False)

        if is_completed:
            for item in (checkbox_item, title_item, id_item, status_item, url_item):
                item.setForeground(QColor("gray"))
                item.setEnabled(False)
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
        else:
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)

        return [checkbox_item, title_item, id_item, status_item, url_item]

    def _adjust_column_sizes(self):
        self.table_view.setColumnWidth(0, 30)

    def _show_context_menu(self, position):
        index = self.table_view.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)
        row = self.proxy_model.mapToSource(index).row()

        if 0 <= row < len(self._all_videos):
            transcript = self._all_videos[row]
            video_id = transcript.video_id
            menu.addAction("Markdown-Datei öffnen", lambda: self._open_transcript_file(video_id))
            menu.addAction("Im Editor-Fenster öffnen", lambda: self._open_in_editor_window(video_id))
            if self._has_transcript(video_id):
                menu.addAction("Starte Kapitelgenerierung", lambda: self._start_chapter_generation(video_id))
            menu.addSeparator()

        select_all_action = QAction("Alle auswählen", self)
        select_all_action.triggered.connect(self._select_all_videos)
        menu.addAction(select_all_action)

        deselect_all_action = QAction("Alle abwählen", self)
        deselect_all_action.triggered.connect(self._deselect_all_videos)
        menu.addAction(deselect_all_action)

        invert_action = QAction("Auswahl umkehren", self)
        invert_action.triggered.connect(self._invert_selection)
        menu.addAction(invert_action)

        menu.exec(self.table_view.mapToGlobal(position))

    def _select_all_videos(self):
        for row in range(self.model.rowCount()):
            checkbox_item = self.model.item(row, 0)
            if checkbox_item and checkbox_item.isEnabled():
                checkbox_item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all_videos(self):
        for row in range(self.model.rowCount()):
            checkbox_item = self.model.item(row, 0)
            if checkbox_item:
                checkbox_item.setCheckState(Qt.CheckState.Unchecked)

    def _invert_selection(self):
        for row in range(self.model.rowCount()):
            checkbox_item = self.model.item(row, 0)
            if checkbox_item and checkbox_item.isEnabled():
                current_state = checkbox_item.checkState()
                new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
                checkbox_item.setCheckState(new_state)

    def _open_transcript_file(self, video_id: str) -> None:
        self.file_open_requested.emit(video_id)

    def _open_in_editor_window(self, video_id: str) -> None:
        from yt_database.gui.widgets.text_file_editor_widget import TextFileEditorWidget

        file_path = self.project_manager_service.get_transcript_path_for_video_id(video_id)
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

    def _start_chapter_generation(self, video_id: str) -> None:
        self.chapter_generation_requested.emit(video_id)

    def _has_transcript(self, video_id: str) -> bool:
        try:
            return self.project_manager_service.has_transcript_lines(video_id)
        except Exception:
            return False


class HyperlinkDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        url = index.data()
        if url and url.startswith("http"):
            painter.save()
            color = QColor(0, 102, 204)
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

# -*- coding: utf-8 -*-
import os
import subprocess
import sys

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileSystemModel, QHeaderView, QLineEdit, QMenu, QTreeView, QVBoxLayout, QWidget

from yt_database.gui.widgets.text_file_editor_widget import TextFileEditorWidget


class ProjectTreeWidget(QWidget):
    file_selected = Signal(str)
    folder_selected = Signal(str)
    chapter_generation_requested = Signal(str)

    def __init__(self, root_path: str, parent=None):
        """
        Initialisiert das TreeView-Widget für die Projektstruktur.

        Args:
            root_path (str): Wurzelverzeichnis für die Anzeige.
            parent: Optionales Parent-Widget.
        """
        super().__init__(parent)
        logger.debug("ProjectTreeWidget: Initialisierung für root_path='{}'", root_path)

        # Setze Mindestgröße für das gesamte Widget
        self.setMinimumSize(250, 400)  # Mindestbreite: 250px, Mindesthöhe: 400px

        # Verbessere die SizePolicy
        from PySide6.QtWidgets import QSizePolicy

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._setup_ui(root_path)

    def _setup_ui(self, root_path: str) -> None:
        """Ruft die UI-Setup-Methoden in der richtigen Reihenfolge auf."""
        self._setup_widgets(root_path)
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self, root_path: str) -> None:
        """Initialisiert alle UI-Komponenten und konfiguriert ihre statischen Eigenschaften."""
        self.model = QFileSystemModel(self)
        self.model.setRootPath(root_path)

        self.tree = QTreeView(self)
        self.tree.setObjectName("projects_tree_view")
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(root_path))
        self.tree.setSortingEnabled(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        # Setze explizite Größen für das TreeView
        self.tree.setMinimumHeight(300)  # Mindesthöhe
        self.tree.setMinimumWidth(250)  # Mindestbreite

        for i in range(1, self.model.columnCount()):
            self.tree.hideColumn(i)

        self.search = QLineEdit(self)
        self.search.setObjectName("projects_tree_search_input")
        self.search.setPlaceholderText("Suche nach Datei- oder Ordnername...")
        self.search.setMaximumHeight(30)  # Begrenze die Höhe des Suchfelds

    def _setup_layouts(self) -> None:
        """Ordnet die initialisierten Widgets in Layouts an."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Kleine Ränder
        layout.setSpacing(5)  # Kleiner Abstand zwischen Widgets

        layout.addWidget(self.search)
        layout.addWidget(self.tree, 1)  # Stretch factor 1 = TreeView bekommt den ganzen Platz

        self.setLayout(layout)

    def _setup_signals(self) -> None:
        """Verbindet die Signale der permanenten Widgets mit ihren Slots."""
        self.search.textChanged.connect(self.on_search)
        self.tree.doubleClicked.connect(self.on_double_click)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position) -> None:
        """Zeigt das Kontextmenü für die Projektstruktur an."""
        logger.debug(f"[ProjectTreeWidget] show_context_menu aufgerufen, position={position}")
        index = self.tree.indexAt(position)
        if not index.isValid():
            logger.warning("[ProjectTreeWidget] show_context_menu: Ungültiger Index an Position")
            return

        file_path = self.model.filePath(index)
        logger.debug(f"[ProjectTreeWidget] Kontextmenü für Datei/Ordner: {file_path}")
        menu = QMenu(self)

        if os.path.isfile(file_path):
            logger.debug("[ProjectTreeWidget] Datei erkannt, füge Dateimenüoptionen hinzu")
            # Dynamische Signal-Verbindungen bleiben hier, wie von den Regeln gefordert.
            menu.addAction("Im Editor öffnen", lambda: self._emit_file_selected(file_path))
            menu.addAction("Im Editor-Fenster öffnen", lambda: self._open_in_editor_window(file_path))

            if file_path.endswith("_transcript.md"):
                logger.debug(f"[ProjectTreeWidget] Kapitelgenerierung-Option verfügbar für: {file_path}")
                menu.addSeparator()
                action = menu.addAction("Starte Kapitelgenerierung")
                action.triggered.connect(
                    lambda checked=False, path=file_path: self._emit_chapter_generation_requested(path)
                )
        elif self.model.isDir(index):
            menu.addAction("Ordner auswählen", lambda: self._emit_folder_selected(file_path))

        menu.addAction("Im Dateimanager öffnen", lambda: self._open_folder_in_file_manager(file_path))

        if not menu.isEmpty():
            menu.exec(self.tree.viewport().mapToGlobal(position))

    def _open_folder_in_file_manager(self, folder_path: str) -> None:
        """Öffnet den angegebenen Ordner im Dateimanager des Betriebssystems."""
        # Der Pfad wird bereits im Kontextmenü validiert, hier direkt verwenden
        target_path = folder_path if os.path.isdir(folder_path) else os.path.dirname(folder_path)

        if sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", target_path])
        elif sys.platform.startswith("win"):
            # explorer.exe kann sowohl Dateien als auch Ordner öffnen
            subprocess.Popen(["explorer", target_path])
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", target_path])

    def _open_in_editor_window(self, file_path: str) -> None:
        """Öffnet die Datei im separaten Editor-Fenster."""
        logger.debug("Öffne Datei im Editor-Fenster: {}", file_path)
        editor = TextFileEditorWidget()
        editor.setWindowTitle(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            editor._content = content
            editor._file_path = file_path
            editor.text_edit.setPlainText(content)
        except Exception as e:
            logger.error(f"Fehler beim Öffnen der Datei im Editor-Fenster: {e}")
        editor.show_as_window()

    # --- Event-Handler ---
    def on_search(self, text: str):
        """
        Sucht rekursiv nach Dateien/Ordnern, die den Suchtext enthalten.
        """
        logger.debug("ProjectTreeWidget: Suche nach '{}'.", text)
        text = text.strip().lower()
        model = self.model
        tree = self.tree
        root = model.index(model.rootPath())

        def match_recursive(parent):
            for row in range(model.rowCount(parent)):
                idx = model.index(row, 0, parent)
                if not idx.isValid():
                    continue
                name = model.fileName(idx).lower()
                # Ich expandiere und scrolle zu jedem Treffer, damit der Nutzer sofort sieht, wo das Ergebnis liegt.
                if text and text in name:
                    tree.expand(idx)
                    tree.scrollTo(idx)
                    tree.setCurrentIndex(idx)
                if model.isDir(idx):
                    match_recursive(idx)

        tree.collapseAll()
        if text:
            match_recursive(root)

    def on_double_click(self, index):
        """Signalisiert, ob ein Ordner oder eine Datei doppelt angeklickt wurde."""
        path = self.model.filePath(index)
        logger.debug("ProjectTreeWidget: Doppelklick auf '{}'.", path)
        if self.model.isDir(index):
            self.folder_selected.emit(path)
        else:
            self.file_selected.emit(path)

    def _emit_file_selected(self, file_path: str) -> None:
        self.file_selected.emit(file_path)

    def _emit_folder_selected(self, file_path: str) -> None:
        self.folder_selected.emit(file_path)

    def _emit_chapter_generation_requested(self, file_path: str) -> None:
        logger.debug(f"[ProjectTreeWidget] chapter_generation_requested.emit({file_path})")
        self.chapter_generation_requested.emit(file_path)

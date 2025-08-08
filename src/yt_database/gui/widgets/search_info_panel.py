# search_info_panel.py – fixed: keine Layouts in _setup_widgets

from typing import Optional, List, Tuple
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QWidget, QPushButton, QTextEdit, QVBoxLayout
from yt_database.models.search_strategy import SearchStrategy, SEARCH_STRATEGIES


class SearchInfoPanel(QFrame):
    strategy_selected = Signal(SearchStrategy)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("search_info_panel")

        self.scroll_area: Optional[QScrollArea] = None

        self._strategy_card_parts: List[Tuple[QFrame, QPushButton, QLabel, QLabel]] = []

        self._strategy_buttons: List[Tuple[QPushButton, SearchStrategy]] = []

        self._current_query = ""

        self._setup_ui()

    # Orchestrierung
    def _setup_ui(self):
        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    # ---------------- Widgets (KEINE LAYOUTS!) ----------------
    def _setup_widgets(self):
        self.title_label = QLabel("Suchstrategien", self)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.strategies_widget = QWidget(self)

        # Karten-Widgets „roh“ erstellen (nur Widgets, keine addWidget-Aufrufe)
        self._strategy_card_parts.clear()
        self._strategy_buttons.clear()
        for info in SEARCH_STRATEGIES:
            card = QFrame(self.strategies_widget)
            name_btn = QPushButton(info.display_name, card)
            desc_lbl = QLabel(info.description, card)
            desc_lbl.setWordWrap(True)
            example_lbl = QLabel(f"Beispiel: {info.example}", card)
            example_lbl.setWordWrap(True)
            self._strategy_card_parts.append((card, name_btn, desc_lbl, example_lbl))
            self._strategy_buttons.append((name_btn, info.strategy))

        self.query_title = QLabel("Generierte FTS5-Query:", self)
        self.query_display = QTextEdit(self)
        self.query_display.setReadOnly(True)
        self.query_display.setPlainText("Gib einen Suchbegriff ein, um die generierte Query zu sehen...")

    # ---------------- Layouts (ALLE Layout-Operationen hier!) ----------------
    def _setup_layouts(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(8)

        # Scroll-Inhalt layouten
        container_layout = QVBoxLayout(self.strategies_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        for card, name_btn, desc_lbl, example_lbl in self._strategy_card_parts:
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(4)
            card_layout.addWidget(name_btn)
            card_layout.addWidget(desc_lbl)
            card_layout.addWidget(example_lbl)
            container_layout.addWidget(card)

        container_layout.addStretch()
        if self.scroll_area is not None:
            self.scroll_area.setWidget(self.strategies_widget)

        # Hauptanordnung
        main.addWidget(self.title_label)
        if self.scroll_area is not None:
            main.addWidget(self.scroll_area)
        main.addWidget(self.query_title)
        main.addWidget(self.query_display)

    # ---------------- Signale ----------------
    def _setup_signals(self):
        for btn, strategy in self._strategy_buttons:
            btn.clicked.connect(lambda _, s=strategy: self.strategy_selected.emit(s))

    # --------- Öffentliche API & Logik (unverändert) ---------
    def update_query_preview(self, query: str, strategy: SearchStrategy):
        self._current_query = query
        if not query or not query.strip():
            self.query_display.setPlainText("Gib einen Suchbegriff ein, um die generierte Query zu sehen...")
            return
        words = query.strip().split()
        if strategy == SearchStrategy.EXACT_PHRASE:
            generated_query = f'"{query.strip()}"'
        elif strategy == SearchStrategy.ALL_WORDS:
            generated_query = " AND ".join(f"{w}*" for w in words) if len(words) > 1 else words[0]
        elif strategy == SearchStrategy.ANY_WORD:
            generated_query = " OR ".join(f"{w}*" for w in words)
        elif strategy == SearchStrategy.FUZZY:
            generated_query = " OR ".join((f"{w}*" if len(w) > 3 else w) for w in words)
        else:  # AUTO
            generated_query = (
                f"{query.strip()}*"
                if len(words) == 1
                else f'("{query.strip()}") OR (' + " AND ".join(f"{w}*" for w in words) + ")"
            )

        self.query_display.setPlainText(
            f"Strategie: {strategy.name}\nEingabe: '{query}'\nFTS5-Query: {generated_query}"
        )

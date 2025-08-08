"""
Separates Info-Fenster für Suchstrategien.

Ein nicht-modales Fenster, das Benutzern eine übersichtliche Darstellung der
verfügbaren Suchstrategien mit Live-Query-Vorschau bietet.
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QTextEdit,
    QGroupBox,
)

from yt_database.models.search_strategy import SearchStrategy, SEARCH_STRATEGIES


class SearchStrategyInfoWindow(QDialog):
    """Ein separates, nicht-modales Fenster für Suchstrategien-Informationen."""

    # --------------------
    # Initialisierung
    # --------------------
    strategy_selected = Signal(SearchStrategy)  # Signal wenn Benutzer eine Strategie auswählt

    def __init__(self, parent=None):
        """Initialisiert das Info-Fenster."""
        super().__init__(parent)
        self.setWindowTitle("Suchstrategien & Query-Hilfe")
        self.setObjectName("search_strategy_info_window")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(False)  # Nicht-modal
        self.resize(500, 700)

        # Aktueller Query-Status
        self._current_query = ""
        self._current_strategy = SearchStrategy.AUTO

        # Auto-Update Timer für bessere Performance
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)

        self._setup_ui()
        self._setup_styles()

    def _setup_ui(self):
        """Initialisiert die UI durch Aufruf der Helper-Methoden."""
        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self):
        """Instanziiert alle UI-Komponenten und konfiguriert sie statisch."""
        # Header
        self.header_frame = QFrame()
        self.header_layout = QVBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.title = QLabel("Erweiterte Suchstrategien")
        self.title.setObjectName("window_title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description = QLabel(
            "Wähle die optimale Suchstrategie für deine Anfrage. "
            "Die Live-Vorschau zeigt dir die generierte FTS5-Query."
        )
        self.description.setObjectName("description")
        self.description.setWordWrap(True)
        self.description.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Query-Vorschau
        self.preview_group = QGroupBox("Live Query-Vorschau")
        self.preview_layout = QVBoxLayout(self.preview_group)
        self.current_status = QLabel("Gib in der Suche einen Begriff ein...")
        self.current_status.setObjectName("query_status")
        self.query_display = QTextEdit()
        self.query_display.setObjectName("query_display")
        self.query_display.setReadOnly(True)
        self.query_display.setMaximumHeight(120)
        self.query_display.setPlainText("Keine aktive Suche")

        # Strategien-Übersicht
        self.strategies_group = QGroupBox("Verfügbare Strategien")
        self.strategies_layout = QVBoxLayout(self.strategies_group)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.strategies_container = QWidget()
        self.container_layout = QVBoxLayout(self.strategies_container)
        self.container_layout.setSpacing(12)
        self.strategy_cards = []
        for strategy_info in SEARCH_STRATEGIES:
            card = self._create_strategy_card(strategy_info)
            self.strategy_cards.append(card)
            self.container_layout.addWidget(card)
        self.container_layout.addStretch()
        self.scroll_area.setWidget(self.strategies_container)

        # Footer
        self.footer_layout = QHBoxLayout()
        self.close_button = QPushButton("Schließen")
        self.close_button.setObjectName("close_button")

    def _setup_layouts(self):
        """Fügt die Komponenten in die Layouts ein und setzt das Hauptlayout."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(16)

        # Header
        self.header_layout.addWidget(self.title)
        self.header_layout.addWidget(self.description)
        self.main_layout.addWidget(self.header_frame)

        # Query-Vorschau
        self.preview_layout.addWidget(self.current_status)
        self.preview_layout.addWidget(self.query_display)
        self.main_layout.addWidget(self.preview_group)

        # Strategien-Übersicht
        self.strategies_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.strategies_group)

        # Footer
        self.footer_layout.addStretch()
        self.footer_layout.addWidget(self.close_button)
        self.main_layout.addLayout(self.footer_layout)

    def _setup_signals(self):
        """Verbindet alle permanenten Signal-Slot-Verbindungen."""
        self._update_timer.timeout.connect(self._perform_query_update)
        self.close_button.clicked.connect(self.close)

    def _setup_styles(self):
        """Definiert die Styles für das Fenster."""

    # --------------------
    # Öffentliche Methoden
    # --------------------
    def show_and_raise(self):
        """Zeigt das Fenster und bringt es in den Vordergrund."""
        self.show()
        self.raise_()
        self.activateWindow()

    def update_query_preview(self, query: str, strategy: SearchStrategy):
        """Aktualisiert die Query-Vorschau (mit Debouncing)."""
        self._current_query = query
        self._current_strategy = strategy

        # Debounce die Updates für bessere Performance
        self._update_timer.stop()
        self._update_timer.start(200)  # 200ms Verzögerung

    # --------------------
    # Event-Handler
    # --------------------
    def _on_strategy_selected(self, strategy: SearchStrategy):
        """Wird ausgelöst, wenn eine Strategie ausgewählt wird."""
        self.strategy_selected.emit(strategy)

        # Visuelles Feedback
        self.current_status.setText(f"Strategie ausgewählt: {strategy.value}")

    def _perform_query_update(self):
        """Führt das eigentliche Query-Update durch."""
        query = self._current_query
        strategy = self._current_strategy

        if not query or not query.strip():
            self.current_status.setText("Gib in der Suche einen Begriff ein...")
            self.query_display.setPlainText("Keine aktive Suche")
            return

        # Status aktualisieren
        strategy_info = next((s for s in SEARCH_STRATEGIES if s.strategy == strategy), None)
        strategy_name = strategy_info.display_name if strategy_info else str(strategy)

        self.current_status.setText(f"Aktuelle Suche: '{query}' mit {strategy_name}")

        # Query generieren und anzeigen
        generated_query = self._simulate_fts_query(query.strip(), strategy)

        display_text = f"Eingabe: {query}\n"
        display_text += f"Strategie: {strategy_name}\n"
        display_text += f"Generierte FTS5-Query:\n{generated_query}\n\n"

        # Erklärung hinzufügen
        explanation = self._get_strategy_explanation(strategy)
        display_text += f"Erklärung: {explanation}"

        self.query_display.setPlainText(display_text)

    # --------------------
    # Hilfsmethoden
    # --------------------
    def _create_strategy_card(self, strategy_info) -> QWidget:
        """Erstellt eine Karte für eine einzelne Strategie."""
        card = QFrame()
        card.setObjectName("strategy_card")
        card.setFrameStyle(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header mit Name und Button
        header_layout = QHBoxLayout()

        # Strategie-Name
        name_label = QLabel(strategy_info.display_name)
        name_label.setObjectName("strategy_name")
        header_layout.addWidget(name_label)

        header_layout.addStretch()

        # Auswahl-Button
        select_button = QPushButton("Auswählen")
        select_button.setObjectName("select_button")
        select_button.clicked.connect(lambda: self._on_strategy_selected(strategy_info.strategy))
        header_layout.addWidget(select_button)

        layout.addLayout(header_layout)

        # Beschreibung
        description = QLabel(strategy_info.description)
        description.setObjectName("strategy_description")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Beispiel
        example_frame = QFrame()
        example_frame.setObjectName("example_frame")
        example_layout = QVBoxLayout(example_frame)
        example_layout.setContentsMargins(8, 8, 8, 8)

        example_label = QLabel("Beispiel:")
        example_label.setObjectName("example_label")
        example_layout.addWidget(example_label)

        example_text = QLabel(strategy_info.example)
        example_text.setObjectName("example_text")
        example_text.setWordWrap(True)
        example_layout.addWidget(example_text)

        layout.addWidget(example_frame)

        return card

    def _simulate_fts_query(self, query: str, strategy: SearchStrategy) -> str:
        """Simuliert die FTS5-Query-Generierung."""
        words = query.split()

        if strategy == SearchStrategy.EXACT_PHRASE:
            return f'"{query}"'
        elif strategy == SearchStrategy.ALL_WORDS:
            if len(words) == 1:
                return query
            return " AND ".join(f"{word}*" for word in words)
        elif strategy == SearchStrategy.ANY_WORD:
            return " OR ".join(f"{word}*" for word in words)
        elif strategy == SearchStrategy.FUZZY:
            fuzzy_words = []
            for word in words:
                if len(word) > 3:
                    fuzzy_words.append(f"{word}*")
                else:
                    fuzzy_words.append(word)
            return " OR ".join(fuzzy_words)
        elif strategy == SearchStrategy.AUTO:
            if len(words) == 1:
                return f"{query}*"
            else:
                exact_phrase = f'"{query}"'
                all_words = " AND ".join(f"{word}*" for word in words)
                return f"({exact_phrase}) OR ({all_words})"
        else:
            return query

    def _get_strategy_explanation(self, strategy: SearchStrategy) -> str:
        """Gibt eine Erklärung der Strategie zurück."""
        explanations = {
            SearchStrategy.AUTO: "Intelligente Auswahl: Versucht sowohl exakte Phrasen als auch AND-Verknüpfung",
            SearchStrategy.EXACT_PHRASE: "Sucht nach der kompletten Eingabe als zusammenhängender Text",
            SearchStrategy.ALL_WORDS: "Alle Wörter müssen im Text vorkommen (AND-Verknüpfung mit Wildcards)",
            SearchStrategy.ANY_WORD: "Mindestens eines der Wörter muss vorkommen (OR-Verknüpfung)",
            SearchStrategy.FUZZY: "Unscharfe Suche mit Wildcards für längere Wörter (>3 Zeichen)",
        }
        return explanations.get(strategy, "Unbekannte Strategie")

## Modulbeschreibung

Das Modul `delegates.py` stellt spezialisierte Delegates für die Darstellung von Item-Views in Qt bereit. Der Hauptfokus liegt auf dem `RichTextHighlightDelegate`, der es ermöglicht, Suchbegriffe innerhalb von Texten farblich hervorzuheben und diese als HTML mittels `QTextDocument` zu rendern. Dadurch werden z.B. Treffer in Suchergebnissen visuell hervorgehoben und die Lesbarkeit verbessert.

## Beteiligte Module & Services

- **Externe Module:**
  - `PySide6.QtCore` (`QRect`, `QRectF`, `Qt`)
  - `PySide6.QtGui` (`QTextDocument`, `QIcon`)
  - `PySide6.QtWidgets` (`QStyle`, `QStyledItemDelegate`)
  - `typing` (`Callable`, `List`)
  - `html` (Escaping von Text)
  - `re` (Reguläre Ausdrücke für Hervorhebung)

- **Interne Module:**
  - Übergibt sich an Item-Views, z.B. in Tabellen oder Listen, die Qt-Delegates unterstützen.

## Workflows

Der Delegate wird typischerweise in folgenden Workflows eingesetzt:

1. **Initialisierung:**
   - Übergabe einer Funktion, die die aktuellen Suchbegriffe liefert (`search_terms_provider`).
   - Optional: Konfiguration der Highlight-Farbe.
2. **Rendering:**
   - Beim Zeichnen eines Items wird der Text per HTML escaped.
   - Alle Suchbegriffe werden im Text gesucht und mit einem farbigen `<span>` hervorgehoben.
   - Das Ergebnis wird als HTML in ein `QTextDocument` gesetzt und im Item gerendert.
3. **Interaktion:**
   - Die Hervorhebung passt sich dynamisch an, wenn sich die Suchbegriffe ändern.
   - Icons werden ebenfalls unterstützt und korrekt positioniert.

**Ablauf (Stichpunkte):**

- Delegate erhält zu rendernden Text und Suchbegriffe.
- Text wird escaped und Suchbegriffe werden per Regex hervorgehoben.
- HTML wird in `QTextDocument` gesetzt und gezeichnet.
- Optionales Icon wird vor dem Text platziert.

## Verarbeitete Datentypen und Datenstrukturen

**Eingaben:**

- `search_terms_provider: Callable[[], List[str]]` — Funktion, die die aktuellen Suchbegriffe liefert.
- `highlight_color: str` — Farbe für die Hervorhebung (Default: Gelb `#FFFF00`).
- Item-Daten (`index.data()`), typischerweise `str`.

**Verarbeitete Daten:**

- Escaped Text (`str`)
- Liste der Suchbegriffe (`List[str]`)
- HTML mit `<span>`-Tags für Hervorhebung
- Qt-Objekte: `QTextDocument`, `QIcon`, `QRect`, `QRectF`, `QStyleOptionViewItem`, `QPainter`

**Ausgaben:**

- Gerenderter Item-Text mit HTML-Hervorhebung im View.
- Optional gerendertes Icon.

## Codebeispiel

```python
from PySide6.QtWidgets import QListView
from src.yt_database.gui.widgets.delegates import RichTextHighlightDelegate

search_terms = lambda: ["Begriff1", "Begriff2"]
delegate = RichTextHighlightDelegate(search_terms, highlight_color="#FFCC00")
view = QListView()
view.setItemDelegate(delegate)
```

## Typdefinitionen

```python
class RichTextHighlightDelegate(QStyledItemDelegate):
    def __init__(self, search_terms_provider: Callable[[], List[str]], highlight_color: str = "#FFFF00"):
        ...
    def _build_highlighted_html(self, plain_text: str) -> str:
        ...
    def paint(self, painter, option, index):
        ...
```

---

Diese Dokumentation bietet eine vollständige Übersicht über die Funktionsweise und Einbindung des `RichTextHighlightDelegate` für Entwickler:innen, die Item-Views mit Suchbegriff-Hervorhebung in Qt realisieren möchten.

"""
Delegates für spezielle Rendering-Aufgaben in Item-Views.

Enthält einen RichTextHighlightDelegate, der Suchbegriffe im Text per HTML
farblich hervorhebt und mittels QTextDocument rendert.
"""

import html
import re
from typing import Callable, List

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QStyle, QStyledItemDelegate


class RichTextHighlightDelegate(QStyledItemDelegate):
    """Rendert Item-Texte mit HTML und hebt gegebene Suchbegriffe hervor.

    search_terms_provider: Callable, die eine aktuelle Liste der Suchbegriffe liefert.
    """

    def __init__(self, search_terms_provider: Callable[[], List[str]], highlight_color: str = "#FFFF00"):
        super().__init__()
        self._get_terms = search_terms_provider
        self._highlight_color = highlight_color

    def _build_highlighted_html(self, plain_text: str) -> str:
        """Erzeugt HTML mit markierten Begriffen. Escaped zunächst den Text."""
        if not plain_text:
            return ""

        escaped = html.escape(plain_text)
        terms = [t for t in (self._get_terms() or []) if t and t.strip()]
        if not terms:
            return escaped

        # Längste zuerst, um Überlappungen zu minimieren
        terms_sorted = sorted(terms, key=len, reverse=True)

        highlighted = escaped
        for term in terms_sorted:
            pattern = re.compile(re.escape(html.escape(term)), re.IGNORECASE)
            highlighted = pattern.sub(
                lambda m: f'<span style="background-color: {self._highlight_color}; color: #000; font-weight: bold;">{m.group()}</span>',
                highlighted,
            )

        return highlighted

    def paint(self, painter, option, index):  # type: ignore[override]
        # Hintergrund/Selektion zeichnen
        painter.save()
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        painter.restore()

        # Icon rendern, falls vorhanden
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if icon is not None:
            from PySide6.QtGui import QIcon

            if isinstance(icon, QIcon) and not icon.isNull():
                icon_size = 16  # Standard-Icon-Größe
                icon_rect = QRect(
                    option.rect.left() + 4,
                    option.rect.top() + (option.rect.height() - icon_size) // 2,
                    icon_size,
                    icon_size,
                )
                icon.paint(painter, icon_rect)
                # Text-Bereich nach rechts verschieben, um Platz für Icon zu schaffen
                text_rect = option.rect.adjusted(icon_size + 8, 0, -4, 0)
            else:
                text_rect = option.rect.adjusted(4, 0, -4, 0)
        else:
            text_rect = option.rect.adjusted(4, 0, -4, 0)

        # Textinhalt und HTML-Hervorhebung
        value = index.data()
        text = "" if value is None else str(value)
        html = self._build_highlighted_html(text)

        # QTextDocument vorbereiten und zeichnen
        painter.save()
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setHtml(html)
        doc.setTextWidth(text_rect.width())
        painter.translate(text_rect.topLeft())
        doc.drawContents(painter, QRectF(0, 0, text_rect.width(), text_rect.height()))
        painter.restore()

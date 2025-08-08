"""
Konfigurationsdatei für das Search Widget.

Ermöglicht die Auswahl zwischen Table- und Tree-Ansicht für Suchergebnisse.
"""

from enum import Enum


class SearchViewMode(Enum):
    """Ansichtsmodi für das Search Widget."""

    TABLE = "table"
    TREE = "tree"


# Standard-Konfiguration
DEFAULT_SEARCH_VIEW_MODE = SearchViewMode.TREE

"""
Datenmodelle für die Such-Funktionalität.
"""

from dataclasses import dataclass


@dataclass
class SearchResult:
    """Typsicheres Datenobjekt für ein einzelnes Suchergebnis mit erweiterten Ranking-Daten."""

    video_title: str
    channel_name: str
    channel_handle: str
    chapter_title: str
    timestamp_url: str
    start_time_str: str
    # Neue Felder für BM25-Ranking und Snippet-Highlighting
    relevance_score: float = 0.0
    highlighted_snippet: str = ""

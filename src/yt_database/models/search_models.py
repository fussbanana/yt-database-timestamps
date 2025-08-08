"""
Datenmodelle für die Such-Funktionalität.
"""

from dataclasses import dataclass


@dataclass
class SearchResult:
    """Typsicheres Datenobjekt für ein einzelnes Suchergebnis."""

    video_title: str
    channel_name: str
    channel_handle: str
    chapter_title: str
    timestamp_url: str
    start_time_str: str

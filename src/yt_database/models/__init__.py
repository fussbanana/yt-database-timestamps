"""
Datenmodelle für yt_database.

Dieses Modul enthält TypedDicts für die strukturierte Arbeit mit Metadaten.

Example:
    >>> from yt_database.models import VideoMetadata
    >>> meta = VideoMetadata(video_titel="Test", video_id="abc", youtube_url="https://...", veroeffentlichungsdatum="2024-01-01", dauer="10:00", kanalname="Testkanal", channel_id="chan123")
    >>> print(meta["video_titel"])
    Test
"""

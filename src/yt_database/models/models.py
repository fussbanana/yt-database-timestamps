from pydantic import BaseModel


class TranscriptEntry(BaseModel):
    text: str
    start: float
    end: float
    duration: float = 0.0
    start_hms: str = ""
    end_hms: str = ""
    duration_hms: str = ""
    speaker: str = ""


class ChapterEntry(BaseModel):
    title: str
    start: float
    end: float
    start_hms: str = ""
    end_hms: str = ""


class TranscriptData(BaseModel):
    title: str = ""
    video_id: str
    channel_id: str
    channel_name: str
    channel_url: str = ""
    channel_handle: str = ""
    video_url: str = ""
    publish_date: str = ""
    duration: str = ""
    entries: list[TranscriptEntry] = []
    chapters: list[ChapterEntry] = []  # Kurze Kapitel für YouTube-Kommentare
    detailed_chapters: list[ChapterEntry] = []  # Detaillierte Kapitel für Datenbank
    error_reason: str = ""

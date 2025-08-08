from typing import List

from loguru import logger


class MockYoutubeMetadataService:
    @staticmethod
    def extract_videos_with_titles(metadata: dict) -> list[tuple[str, str]]:
        """
        Gibt eine Dummy-Liste von (video_id, video_titel)-Tupeln für Tests zurück.
        """
        entries = metadata.get("entries", [])
        return [(entry.get("id", "mock_id"), entry.get("title", "Mock Transcript")) for entry in entries]

    """Mock für YoutubeMetadataService."""

    def __init__(self, settings=None):
        pass

    # KORRIGIERT: Signatur und Rückgabetyp an Protokoll angepasst
    def fetch_video_metadata(self, video_id: str) -> dict:
        logger.info(f"[MOCK] fetch_metadata aufgerufen für {video_id}")
        return {
            "id": "@mock_channel",
            "video_titel": "MOCK_TITLE",
            "video_id": video_id,
            "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
            "veroeffentlichungsdatum": "2024-01-01",
            "dauer": "10:00",
            "kanalname": "Mock Kanal",
            "channel_id": "UC_mock_channel_id",
        }

    # KORRIGIERT: Fehlende Methode hinzugefügt
    def fetch_channel_metadata(self, channel_url: str) -> dict:
        logger.info(f"[MOCK] fetch_channel_metadata aufgerufen für {channel_url}")
        return {
            "id": "@mock_channel",
            "title": "Mock Kanal",
            "entries": [{"id": "mock_id_1"}, {"id": "mock_id_2"}],
        }

    # KORRIGIERT: Fehlende Methode hinzugefügt
    def get_video_ids(self, channel_metadata: dict) -> List[str]:
        logger.info("[MOCK] get_video_ids aufgerufen")
        return ["mock_id_1", "mock_id_2"]

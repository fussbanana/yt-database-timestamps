from typing import Any, Dict, Set, Tuple  # <-- Set und Tuple importieren

from loguru import logger


class MockProjectManagerService:
    def get_all_channels(self):
        return []

    def get_videos_for_channel(self, channel_id):
        return []

    def add_videos_to_channel(self, channel_id, videos_data):
        pass

    def mark_as_chaptered(self, video_id):
        pass

    def write_transcript_with_status(self, video_id, formatted, metadata):
        pass

    def get_transcript_path_for_video_id(self, video_id, channel_handle=None):
        return f"mock_path_{video_id}.md"

    """Mock für ProjectManagerService."""

    def __init__(self, settings=None) -> None:
        # Hier die Typ-Annotation hinzufügen
        self.created_projects: Set[Tuple[str, str]] = set()
        self.index: Dict[str, Any] = {}
        self.channel_index: Dict[str, Any] = {}

    def create_project(self, id: str, video_id: str) -> None:
        logger.info(f"[MOCK] create_project aufgerufen für {id}/{video_id}")
        self.created_projects.add((id, video_id))

    def update_index(self, video_id: str, metadata: dict) -> None:
        logger.info(f"[MOCK] update_index aufgerufen für {video_id}")
        self.index[video_id] = metadata

    def is_transcribed(self, video_id: str) -> bool:
        logger.info(f"[MOCK] is_transcribed aufgerufen für {video_id}")
        return video_id in self.index

    def update_channel_index(self, channel_id: str, metadata: Dict[str, Any]) -> None:
        logger.info(f"[MOCK] update_channel_index aufgerufen für {channel_id}")
        self.channel_index[channel_id] = metadata

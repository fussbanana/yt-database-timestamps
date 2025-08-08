from typing import Any, Dict, List, Optional

from loguru import logger


class MockTranscriptService:
    """Mock für TranscriptService."""

    def __init__(self, settings=None):
        pass

    def get_transcript(self, video_id: str):
        logger.info(f"[MOCK] get_transcript aufgerufen für {video_id}")
        return f"MOCK_TRANSCRIPT({video_id})"

    # KORRIGIERT: Signatur an das Protokoll angepasst
    def fetch_transcript(self, video_id: str, languages: Optional[List[str]] = None) -> Dict[str, Any]:
        logger.info(f"[MOCK] fetch_transcript aufgerufen für {video_id} mit Sprachen {languages}")
        return {
            "transcript": [{"text": "Mock-Text", "start": 0.0, "duration": 1.0}],
            "metadata": {"video_id": video_id, "mock": True},
        }

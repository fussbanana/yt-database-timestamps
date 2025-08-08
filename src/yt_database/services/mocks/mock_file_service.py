from typing import Any

from yt_database.utils.utils import to_snake_case


class MockFileService:
    """Mock für FileService."""

    def __init__(self, settings=None):
        self.writes = []

    def write(self, path: str, content: Any) -> None:
        """Schreibt Mock-Daten in eine Datei und speichert sie für Tests.

        Args:
            path (str): Pfad zur Datei.
            content (Any): Inhalt, der geschrieben werden soll.
        """
        self.writes.append((path, content))
        print(f"[MockFileService] write: {path} <- {content}")

    # KORRIGIERT: Signatur an das Protokoll angepasst
    def write_transcript_file(self, formatted: str, metadata: dict) -> None:
        channel_id = metadata["id"]
        video_id = metadata["video_id"]
        video_title = metadata["video_titel"]
        safe_title = to_snake_case(video_title)
        filename = f"projects/{channel_id}/{video_id}/{safe_title}_transcript.txt"
        self.write(filename, formatted)

    def read(self, path: str) -> str:
        """Mock-Leseoperation: Gibt einen Dummy-String zurück."""
        return f"Mocked content for {path}"

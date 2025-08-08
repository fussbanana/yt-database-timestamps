"""
Testet das Einlesen und die Status-Erkennung einer echten Transkriptdatei.
"""

import pytest
import os
from yt_database.utils.utils import has_content_after_marker


@pytest.fixture
def transcript_file_path(tmp_path):
    # Kopiere die Beispiel-Transkriptdatei ins temporäre Testverzeichnis
    src = os.path.join(os.path.dirname(__file__), "../test_transcript_example.md")
    dst = tmp_path / "test_transcript_example.md"
    with open(src, "r", encoding="utf-8") as f_in, open(dst, "w", encoding="utf-8") as f_out:
        f_out.write(f_in.read())
    return str(dst)


def test_transcript_has_content(transcript_file_path):
    # Prüfe, ob nach dem Transkript-Marker Inhalt vorhanden ist
    assert has_content_after_marker(transcript_file_path, "## Transkript", False, 4)

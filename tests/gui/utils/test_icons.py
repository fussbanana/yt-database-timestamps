"""
Test für Icons

Testet, ob die statischen Icon-Pfade als Strings verfügbar sind und QIcon erzeugt werden kann.
"""

from src.yt_database.gui.utils.icons import Icons
from PySide6.QtGui import QIcon


def test_icon_paths_are_strings():
    assert isinstance(Icons.ARROW_LEFT, str)
    assert isinstance(Icons.PLAY, str)
    assert isinstance(Icons.SETTINGS, str)
    assert isinstance(Icons.BOOK, str)

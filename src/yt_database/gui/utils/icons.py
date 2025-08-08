"""Icon utilities for accessing QRC-embedded icons throughout the application.

This module provides a centralized way to access icons from the compiled
QRC resource file, ensuring consistent icon usage across all widgets.
"""

from PySide6.QtGui import QIcon

# Ensure icons_rc is imported to register the resources
from yt_database.resources import icons_rc  # noqa: F401


class Icons:
    """Centralized icon access for the application.

    This class provides consistent access to all available icons
    from the QRC resource system. Icons are organized by category
    and provide semantic naming.
    """

    # Navigation Icons
    ARROW_LEFT = ":/feather/arrow-left.png"
    ARROW_RIGHT = ":/feather/arrow-right.png"
    ARROW_UP = ":/feather/arrow-up.png"
    ARROW_DOWN = ":/feather/arrow-down.png"
    CHEVRON_LEFT = ":/feather/chevron-left.png"
    CHEVRON_RIGHT = ":/feather/chevron-right.png"
    CHEVRON_UP = ":/feather/chevron-up.png"
    CHEVRON_DOWN = ":/feather/chevron-down.png"

    # Action Icons
    PLAY = ":/feather/play.png"
    PAUSE = ":/feather/pause.png"
    STOP = ":/feather/stop-circle.png"
    REFRESH = ":/feather/refresh-cw.png"
    DOWNLOAD = ":/feather/download.png"
    UPLOAD = ":/feather/upload.png"

    # File & Folder Icons
    FILE = ":/feather/file.png"
    FILE_TEXT = ":/feather/file-text.png"
    FOLDER = ":/feather/folder.png"
    FOLDER_OPEN = ":/feather/folder-plus.png"
    SAVE = ":/feather/save.png"

    # UI Icons
    SETTINGS = ":/icons/settings.svg"
    SEARCH = ":/feather/search.png"
    MENU = ":/feather/menu.png"
    HOME = ":/feather/home.png"
    INFO = ":/feather/info.png"
    HELP = ":/feather/help-circle.png"
    NOTEBOOK = ":/icons/notebooklm.svg"
    PROMPT = ":/icons/prompt_icon.svg"
    SEND_TO_NOTEBOOK = ":/icons/send_to_notebooklm.svg"
    MAGNIFY = ":/icons/magnifying-glass.png"

    # Content Icons
    BOOK = ":/feather/book.png"
    BOOK_OPEN = ":/feather/book-open.png"
    EDIT = ":/feather/edit.png"
    EYE = ":/feather/eye.png"
    EYE_OFF = ":/feather/eye-off.png"

    # Status Icons
    CHECK = ":/feather/check.png"
    CHECK_CIRCLE = ":/feather/check-circle.png"
    X = ":/feather/x.png"
    X_CIRCLE = ":/feather/x-circle.png"
    ALERT = ":/feather/alert-triangle.png"
    WARNING = ":/feather/warning-triangle.png"
    HOURGLASS = ":/feather/hourglass.png"
    PAPER = ":/feather/paper.png"

    # Database Icons
    DATABASE = ":/feather/database.png"
    ARCHIVE = ":/feather/archive.png"

    # Communication Icons
    MAIL = ":/feather/mail.png"
    MESSAGE = ":/feather/message-circle.png"

    # Media Icons
    VIDEO = ":/feather/video.png"
    MUSIC = ":/feather/music.png"
    VOLUME = ":/feather/volume-2.png"

    @staticmethod
    def get(icon_path: str) -> QIcon:
        """Get a QIcon from the given resource path.

        Args:
            icon_path (str): The QRC resource path (e.g., ":/feather/settings.png")

        Returns:
            QIcon: The loaded icon
        """
        return QIcon(icon_path)

    @staticmethod
    def settings() -> QIcon:
        """Get the settings icon."""
        return QIcon(Icons.SETTINGS)

    @staticmethod
    def book_open() -> QIcon:
        """Get the book-open icon."""
        return QIcon(Icons.BOOK_OPEN)

    @staticmethod
    def search() -> QIcon:
        """Get the search icon."""
        return QIcon(Icons.SEARCH)

    @staticmethod
    def database() -> QIcon:
        """Get the database icon."""
        return QIcon(Icons.DATABASE)

    @staticmethod
    def notebook() -> QIcon:
        """Get the NotebookLM icon."""
        return QIcon(Icons.NOTEBOOK)

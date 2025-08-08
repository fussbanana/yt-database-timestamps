# src/yt_database/gui/components/style_manager.py
from __future__ import annotations

from loguru import logger
from PySide6.QtCore import QFileSystemWatcher, QObject, Slot
from PySide6.QtWidgets import QApplication

from yt_database.config.settings import STYLESHEET_FILE


class StyleManager(QObject):
    """
    Verwaltet das Laden und Live-Neuladen des Anwendungs-Stylesheets.
    """

    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self.app = app
        self._watcher = QFileSystemWatcher()

        if STYLESHEET_FILE.exists():
            self._watcher.addPath(str(STYLESHEET_FILE))
            self._watcher.fileChanged.connect(self.reload_stylesheet)
            logger.info(f"StyleManager: Beobachte Stylesheet für Live-Reload: {STYLESHEET_FILE}")
        else:
            logger.warning(f"StyleManager: Stylesheet-Datei nicht gefunden, Live-Reload deaktiviert: {STYLESHEET_FILE}")

        self.reload_stylesheet()

    @Slot()
    def reload_stylesheet(self):
        """Liest die QSS-Datei und wendet sie auf die gesamte Anwendung an."""
        logger.debug("StyleManager: Stylesheet wird neu geladen...")
        try:
            with open(STYLESHEET_FILE, "r", encoding="utf-8") as f:
                style = f.read()
                self.app.setStyleSheet(style)
        except FileNotFoundError:
            logger.warning(f"StyleManager: Stylesheet-Datei '{STYLESHEET_FILE}' konnte nicht geladen werden.")
        except Exception as e:
            logger.error(f"StyleManager: Fehler beim Laden des Stylesheets: {e}")

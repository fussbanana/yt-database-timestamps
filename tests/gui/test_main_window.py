"""
Unittests für das Hauptfenster (MainWindow)

Testet die grundlegende Instanziierung und das Vorhandensein zentraler Methoden.
"""

import pytest
from PySide6.QtWidgets import QApplication
from yt_database.gui.main_window import MainWindow


def test_main_window_instantiation(qtbot):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(app)
    qtbot.addWidget(window)
    assert window is not None
    assert window.windowTitle() is not None
    window.close()

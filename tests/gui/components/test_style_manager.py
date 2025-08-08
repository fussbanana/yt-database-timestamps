"""
Test für StyleManager

Testet die Instanziierung und das Aufrufen von reload_stylesheet mit Dummy-QApplication.
"""

import pytest
from src.yt_database.gui.components.style_manager import StyleManager

class DummyApp:
    def setStyleSheet(self, style):
        self.style = style

def test_style_manager_instantiation_runs(monkeypatch):
    app = DummyApp()
    manager = StyleManager(app)
    # Teste, dass reload_stylesheet ohne Exception aufgerufen werden kann
    manager.reload_stylesheet()

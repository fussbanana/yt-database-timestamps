"""
Test für UiManager

Testet die Instanziierung des UiManager mit Dummy-Abhängigkeiten.
"""

import pytest
from src.yt_database.gui.components.ui_manager import UiManager

class DummyMainWindow:
    pass

class DummyServiceFactory:
    pass

class DummyFontManager:
    pass

def test_ui_manager_instantiation():
    main_window = DummyMainWindow()
    service_factory = DummyServiceFactory()
    font_manager = DummyFontManager()
    manager = UiManager(main_window, service_factory, font_manager)
    assert manager.main_window is main_window
    assert manager.service_factory is service_factory
    assert manager.font_manager is font_manager

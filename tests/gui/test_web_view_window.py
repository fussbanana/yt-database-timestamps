"""
Unittests für das WebEngineWindow (web_view_window.py)

Testet die grundlegende Instanziierung des WebEngineWindow.
"""

import pytest
from PySide6.QtWidgets import QApplication
from yt_database.gui.web_view_window import WebEngineWindow

from yt_database.services.service_factory import ServiceFactory


# Dummy-Implementierungen für alle benötigten Services

class DummyFileService:
    def __init__(self, *args, **kwargs):
        pass

class DummyAnalysisPromptService:
    def __init__(self, *args, **kwargs):
        pass

class DummySelectorService:
    def __init__(self, *args, **kwargs):
        pass

class DummyWebAutomationService:
    def __init__(self, *args, **kwargs):
        pass

def test_web_engine_window_instantiation(qtbot):
    app = QApplication.instance() or QApplication([])
    factory = ServiceFactory(
        file_service_class=DummyFileService,
        analysis_prompt_service_class=DummyAnalysisPromptService,
        selector_service_class=DummySelectorService,
        web_automation_service_class=DummyWebAutomationService
    )
    window = WebEngineWindow(service_factory=factory)
    qtbot.addWidget(window)
    assert window is not None
    window.close()

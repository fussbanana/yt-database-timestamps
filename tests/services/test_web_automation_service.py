# -*- coding: utf-8 -*-
"""
Unittests für den WebAutomationService (Smoke-Test).
"""

import pytest
from unittest.mock import MagicMock
from yt_database.services.web_automation_service import WebAutomationService


def test_web_automation_service_instantiation():
    """Testet die Instanziierung mit gemockten Abhängigkeiten."""
    mock_page = MagicMock()
    mock_selectors = MagicMock()
    service = WebAutomationService(page=mock_page, selectors=mock_selectors)
    assert service._page is mock_page
    assert service.selectors is mock_selectors


def test_web_automation_service_missing_args():
    """Testet, dass ein ValueError geworfen wird, wenn page oder selectors fehlen."""
    mock_page = MagicMock()
    mock_selectors = MagicMock()
    with pytest.raises(ValueError):
        WebAutomationService(page=None, selectors=mock_selectors)
    with pytest.raises(ValueError):
        WebAutomationService(page=mock_page, selectors=None)

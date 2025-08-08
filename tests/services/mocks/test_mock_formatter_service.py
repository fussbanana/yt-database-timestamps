"""
Unit-Tests für MockFormatterService.

Testet die Rückgabe des festen Mock-Strings.
"""

import pytest

from yt_database.services.mocks.mock_formatter_service import MockFormatterService


@pytest.mark.unit
class TestMockFormatterService:
    def test_format_returns_mock_string(self):
        service = MockFormatterService()
        result = service.format({}, {})
        assert result.startswith("MOCK-HEADER")
        assert "MOCK-TRANSKRIPT" in result

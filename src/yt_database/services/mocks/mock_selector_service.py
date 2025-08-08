# src/yt_database/services/mocks/mock_selector_service.py
from yt_database.services.protocols import SelectorServiceProtocol


class MockSelectorService(SelectorServiceProtocol):
    """Mock für SelectorServiceProtocol. Gibt Dummy-Selektoren zurück."""

    def get_selectors(self):
        return {}

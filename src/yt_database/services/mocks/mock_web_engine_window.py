# src/yt_database/services/mocks/mock_web_engine_window.py
from yt_database.services.protocols import WebEngineWindowProtocol


class MockWebEngineWindow(WebEngineWindowProtocol):
    """Mock für WebEngineWindowProtocol. Stellt Dummy-Fenster bereit."""

    def show(self):
        pass

# src/yt_database/services/mocks/mock_web_automation_service.py
from yt_database.services.protocols import WebAutomationServiceProtocol


class MockWebAutomationService(WebAutomationServiceProtocol):
    """Mock für WebAutomationServiceProtocol. Simuliert Web-Aktionen."""

    def run_sequence(self, sequence_name: str) -> bool:
        return True

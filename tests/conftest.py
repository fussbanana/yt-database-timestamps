import pytest
from PySide6.QtCore import QObject
from peewee import SqliteDatabase


@pytest.fixture
def service_factory():
    """Dummy-ServiceFactory für WebEngineWindow-Tests."""

    class DummyServiceFactory:
        def get_file_service(self):
            class DummyFileService:
                def read(self, path):
                    return ""

            return DummyFileService()

        def get_web_automation_service(self, page=None):
            class DummyWebAutomationService:
                pass

            return DummyWebAutomationService()

        def get_formatter_service(self):
            class DummyFormatterService:
                pass

            return DummyFormatterService()

        def get_project_manager_service(self):
            class DummyProjectManagerService:
                pass

            return DummyProjectManagerService()

        def get_transcript_service(self):
            class DummyTranscriptService:
                pass

            return DummyTranscriptService()

    return DummyServiceFactory()


@pytest.fixture
def qt_parent():
    """Stellt ein langlebiges QObject-Parent-Objekt für alle Qt-basierten Tests bereit."""
    parent = QObject()
    yield parent
    parent.deleteLater()


@pytest.fixture(scope="session")
def test_db():
    """Stellt eine isolierte In-Memory-Datenbank für alle Tests bereit."""
    db = SqliteDatabase(":memory:")
    db.connect()
    yield db
    db.close()

import pytest
from unittest.mock import MagicMock, patch
from yt_database.services.project_manager_service import ProjectManagerService


@pytest.fixture
def mock_settings():
    return MagicMock()


@pytest.fixture
def service(mock_settings, test_db, monkeypatch):
    # Monkeypatch das globale db-Objekt auf die Testdatenbank
    monkeypatch.setattr("yt_database.database.db", test_db)
    from unittest.mock import MagicMock

    mock_file_service = MagicMock()
    return ProjectManagerService(settings=mock_settings, file_service=mock_file_service)


def test_add_videos_to_channel_success(service, monkeypatch):
    mock_channel = MagicMock()
    mock_video = MagicMock()
    monkeypatch.setattr("yt_database.services.project_manager_service.Channel.get", lambda **kwargs: mock_channel)
    monkeypatch.setattr(
        "yt_database.services.project_manager_service.Transcript.get_or_create", lambda **kwargs: (mock_video, True)
    )
    monkeypatch.setattr(
        "yt_database.services.project_manager_service.db.atomic",
        lambda: MagicMock(__enter__=lambda s: None, __exit__=lambda s, a, b, c: None),
    )
    service.add_videos_to_channel("chanid", [{"video_id": "vid1", "title": "t1"}])


def test_update_channel_index(service, monkeypatch):
    monkeypatch.setattr(
        "yt_database.services.project_manager_service.Channel.replace", lambda **kwargs: MagicMock(execute=lambda: None)
    )
    monkeypatch.setattr(
        "yt_database.services.project_manager_service.db.atomic",
        lambda: MagicMock(__enter__=lambda s: None, __exit__=lambda s, a, b, c: None),
    )
    service.update_channel_index("chanid", {"id": "chanid", "channel_name": "Test", "channel_url": "url"})


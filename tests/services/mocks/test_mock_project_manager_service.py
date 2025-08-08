"""
Unit-Tests für MockProjectManagerService.

Testet das Anlegen von Projekten und das Aktualisieren des Index im Speicher.
"""

import pytest

from yt_database.services.mocks.mock_project_manager_service import MockProjectManagerService


@pytest.mark.unit
class TestMockProjectManagerService:
    def test_create_project_adds_to_created_projects(self):
        service = MockProjectManagerService()
        id = "testid"
        video_id = "abc123"
        service.create_project(id, video_id)
        assert (id, video_id) in service.created_projects

    def test_update_index_sets_metadata(self):
        service = MockProjectManagerService()
        service.update_index("xyz789", {"title": "Testvideo"})
        assert service.index["xyz789"]["title"] == "Testvideo"

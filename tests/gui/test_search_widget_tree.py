"""
Tests für das SearchWidgetTree - TreeView-basierte Suchfunktionalität.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from yt_database.gui.widgets.search_widget_tree import SearchWidgetTree
from yt_database.models.search_models import SearchResult


def test_search_widget_tree_import():
    """Test, dass das SearchWidgetTree korrekt importiert werden kann."""
    from yt_database.gui.widgets.search_widget_tree import SearchWidgetTree

    assert SearchWidgetTree is not None


@pytest.fixture
def search_widget_tree(qtbot):
    """Fixture für ein SearchWidgetTree Widget."""
    widget = SearchWidgetTree()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def sample_search_results():
    """Fixture für Beispiel-Suchergebnisse."""
    return [
        SearchResult(
            video_title="Python Tutorial: Advanced Features",
            chapter_title="List Comprehensions und Generators",
            timestamp_url="https://youtu.be/example1?t=120s",
            start_time_str="00:02:00",
            channel_name="Python Learning",
            channel_handle="@pythonlearning"
        ),
        SearchResult(
            video_title="Python Tutorial: Advanced Features",
            chapter_title="Decorators und Context Managers",
            timestamp_url="https://youtu.be/example1?t=450s",
            start_time_str="00:07:30",
            channel_name="Python Learning",
            channel_handle="@pythonlearning"
        ),
        SearchResult(
            video_title="Web Development with Django",
            chapter_title="Model-View-Template Pattern",
            timestamp_url="https://youtu.be/example2?t=350s",
            start_time_str="00:05:50",
            channel_name="Django Tutorials",
            channel_handle="@djangotutorials"
        ),
    ]


class TestSearchWidgetTree:
    """Tests für das SearchWidgetTree Widget."""

    def test_widget_initialization(self, search_widget_tree):
        """Test, dass das Widget korrekt initialisiert wird."""
        assert search_widget_tree.windowTitle() == "Erweiterte Suche"
        assert search_widget_tree.search_input is not None
        assert search_widget_tree.search_button is not None
        assert search_widget_tree.results_tree is not None
        assert search_widget_tree.status_label is not None

    def test_empty_search_displays_status(self, search_widget_tree, qtbot):
        """Test, dass bei leerer Suche ein Status angezeigt wird."""
        # Widget sichtbar machen für Tests
        search_widget_tree.show()
        qtbot.waitForWindowShown(search_widget_tree)

        # Leere Suchergebnisse anzeigen
        search_widget_tree.display_results([])

        assert search_widget_tree.status_label.isVisible()
        assert "Keine Ergebnisse" in search_widget_tree.status_label.text()
        assert not search_widget_tree.results_tree.isVisible()

    def test_display_results_creates_tree_structure(self, search_widget_tree, sample_search_results, qtbot):
        """Test, dass Suchergebnisse korrekt als Baumstruktur angezeigt werden."""
        # Widget sichtbar machen für Tests
        search_widget_tree.show()
        qtbot.waitForWindowShown(search_widget_tree)

        search_widget_tree.display_results(sample_search_results)

        # Tree sollte sichtbar sein, Status versteckt
        assert search_widget_tree.results_tree.isVisible()
        assert not search_widget_tree.status_label.isVisible()

        # Model sollte 2 Top-Level-Items haben (2 verschiedene Videos)
        model = search_widget_tree.results_model
        assert model.rowCount() == 2

        # Erstes Video sollte 2 Kapitel haben
        video_item = model.item(0, 0)
        assert video_item.rowCount() == 2

        # Zweites Video sollte 1 Kapitel haben
        video_item = model.item(1, 0)
        assert video_item.rowCount() == 1

    def test_video_items_have_no_links(self, search_widget_tree, sample_search_results):
        """Test, dass Video-Items keine Links haben."""
        search_widget_tree.display_results(sample_search_results)

        model = search_widget_tree.results_model
        video_item = model.item(0, 0)

        # Video-Item sollte keinen Link haben
        assert video_item.data(Qt.ItemDataRole.UserRole) is None

    def test_chapter_items_have_links(self, search_widget_tree, sample_search_results):
        """Test, dass Kapitel-Items Links haben."""
        search_widget_tree.display_results(sample_search_results)

        model = search_widget_tree.results_model
        video_item = model.item(0, 0)
        chapter_item = video_item.child(0, 0)

        # Kapitel-Item sollte einen Link haben (ein beliebiger aus den Beispieldaten)
        link = chapter_item.data(Qt.ItemDataRole.UserRole)
        assert link is not None
        assert "https://youtu.be/example" in link
        assert "?t=" in link

    def test_search_button_click_emits_signal(self, search_widget_tree, qtbot):
        """Test, dass Klick auf Suchen-Button das Signal auslöst."""
        with qtbot.waitSignal(search_widget_tree.search_requested, timeout=1000) as blocker:
            search_widget_tree.search_input.setText("test keyword")
            search_widget_tree.search_button.click()

        assert blocker.args == ["test keyword"]

    def test_enter_key_emits_signal(self, search_widget_tree, qtbot):
        """Test, dass Enter-Taste das Signal auslöst."""
        with qtbot.waitSignal(search_widget_tree.search_requested, timeout=1000) as blocker:
            search_widget_tree.search_input.setText("test keyword")
            qtbot.keyPress(search_widget_tree.search_input, Qt.Key.Key_Return)

        assert blocker.args == ["test keyword"]

    def test_empty_search_string_does_not_emit_signal(self, search_widget_tree, qtbot):
        """Test, dass leere Suchstrings kein Signal auslösen."""
        search_widget_tree.search_input.setText("   ")  # Nur Leerzeichen

        # Signal sollte nicht ausgelöst werden
        with pytest.raises(qtbot.TimeoutError):
            with qtbot.waitSignal(search_widget_tree.search_requested, timeout=500):
                search_widget_tree.search_button.click()

    def test_many_videos_not_auto_expanded(self, search_widget_tree):
        """Test, dass bei vielen Videos der Tree nicht automatisch expandiert wird."""
        # Erstelle viele Suchergebnisse (> 5 Videos)
        many_results = []
        for i in range(7):
            many_results.append(SearchResult(
                video_title=f"Video {i}",
                chapter_title=f"Kapitel {i}",
                timestamp_url=f"https://youtu.be/example{i}?t=120s",
                start_time_str="00:02:00",
                channel_name=f"Channel {i}",
                channel_handle=f"@channel{i}"
            ))

        search_widget_tree.display_results(many_results)

        # Tree sollte nicht automatisch expandiert sein
        model = search_widget_tree.results_model
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            assert not search_widget_tree.results_tree.isExpanded(index)

"""
Rudimentärer Test für VideoSelectionTableWidget
"""


def test_video_selection_table_widget_import():
    from yt_database.gui.widgets.video_selection_table_widget import VideoSelectionTableWidget

    assert VideoSelectionTableWidget is not None

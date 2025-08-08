"""
Rudimentärer Test für DatabaseOverviewWidget
"""


def test_database_table_view_widget_import():
    from yt_database.gui.widgets.database_table_view_widget import DatabaseOverviewWidget

    assert DatabaseOverviewWidget is not None

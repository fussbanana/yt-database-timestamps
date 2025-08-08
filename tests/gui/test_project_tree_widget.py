"""
Rudimentärer Test für ProjectTreeWidget
"""


def test_projects_tree_view_widget_import():
    from yt_database.gui.widgets.projects_tree_view_widget import ProjectTreeWidget

    assert ProjectTreeWidget is not None

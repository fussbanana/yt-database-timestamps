"""
Rudimentärer Test für ConfigDialog
"""


def test_config_dialog_import():
    from yt_database.gui.widgets.config_dialog import ConfigDialog

    assert ConfigDialog is not None

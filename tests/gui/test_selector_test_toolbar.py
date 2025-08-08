"""
Rudimentärer Test für SelectorTestToolbar
"""


def test_selector_test_toolbar_import():
    from yt_database.gui.widgets.selector_test_toolbar import SelectorTestToolbar

    assert SelectorTestToolbar is not None

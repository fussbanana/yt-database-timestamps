"""
Rudimentärer Test für SelectorService
"""


def test_selector_service_import():
    from yt_database.services.selector_service import SelectorService

    assert SelectorService is not None

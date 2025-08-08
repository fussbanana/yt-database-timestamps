"""
Rudimentärer Test für ServiceFactory
"""


def test_service_factory_import():
    from yt_database.services.service_factory import ServiceFactory

    assert ServiceFactory is not None

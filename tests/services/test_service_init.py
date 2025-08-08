"""
Rudimentärer Test für __init__-Import
"""


def test_services_init_import():
    import yt_database.services

    assert yt_database.services is not None

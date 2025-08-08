"""
Rudimentärer Test für __init__-Import
"""


def test_database_init_import():
    import yt_database.database

    assert yt_database.database is not None

"""
Rudimentärer Test für __init__-Import
"""


def test_utils_init_import():
    import yt_database.utils

    assert yt_database.utils is not None

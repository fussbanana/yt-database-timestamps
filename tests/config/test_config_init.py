"""
Rudimentärer Test für __init__-Import
"""


def test_config_init_import():
    import yt_database.config

    assert yt_database.config is not None

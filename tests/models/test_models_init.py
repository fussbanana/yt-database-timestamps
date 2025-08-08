"""
Rudimentärer Test für __init__-Import
"""


def test_models_init_import():
    import yt_database.models

    assert yt_database.models is not None

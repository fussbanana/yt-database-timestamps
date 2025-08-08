"""
Rudimentärer Test für GeneratorService
"""


def test_generator_service_import():
    from yt_database.services.generator_service import GeneratorService

    assert GeneratorService is not None

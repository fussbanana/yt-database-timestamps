"""
Rudimentärer Test für Protocols
"""


def test_protocols_import():
    from yt_database.services.protocols import (
        BatchTranscriptionServiceProtocol,
        GeneratorServiceProtocol,
        ProjectManagerProtocol,
    )

    assert BatchTranscriptionServiceProtocol is not None
    assert GeneratorServiceProtocol is not None
    assert ProjectManagerProtocol is not None

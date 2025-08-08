"""
Rudimentärer Test für SingleTranscriptionWorker
"""


def test_single_transcription_worker_import():
    from yt_database.services.single_transcription_worker import SingleTranscriptionWorker

    assert SingleTranscriptionWorker is not None

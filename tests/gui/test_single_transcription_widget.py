"""
Rudimentärer Test für SingleTranscriptionWidget
"""


def test_single_transcription_widget_import():
    from yt_database.gui.widgets.single_transcription_widget import SingleTranscriptionWidget

    assert SingleTranscriptionWidget is not None

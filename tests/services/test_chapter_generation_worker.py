"""
Rudimentärer Test für ChapterGenerationWorker
"""


def test_chapter_generation_worker_import():
    from yt_database.services.chapter_generation_worker import ChapterGenerationWorker

    assert ChapterGenerationWorker is not None

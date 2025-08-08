"""
Tests for the search_models module.
"""

from yt_database.models.search_models import SearchResult


def test_search_result_instantiation():
    """
    Tests the instantiation of the SearchResult dataclass.
    """
    video_title = "Test Video"
    chapter_title = "Test Chapter"
    timestamp_url = "http://example.com/video?t=123"
    start_time_str = "02:03"
    channel_name = "Test Channel"
    channel_handle = "@testchannel"

    result = SearchResult(
        video_title=video_title,
        chapter_title=chapter_title,
        timestamp_url=timestamp_url,
        start_time_str=start_time_str,
        channel_name=channel_name,
        channel_handle=channel_handle,
    )

    assert result.video_title == video_title
    assert result.chapter_title == chapter_title
    assert result.timestamp_url == timestamp_url
    assert result.start_time_str == start_time_str
    assert result.channel_name == channel_name
    assert result.channel_handle == channel_handle
"""Tests for YouTube feed URL builder."""

import pytest

from tech_tracker.sources.youtube.rss import build_youtube_feed_url


def test_build_url_normal() -> None:
    """Test building URL with normal channel ID."""
    channel_id = "UC1234567890"
    expected = "https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890"
    
    result = build_youtube_feed_url(channel_id)
    
    assert result == expected


def test_build_url_trims() -> None:
    """Test building URL with channel ID that has whitespace."""
    channel_id = "  UC1234567890  "
    expected = "https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890"
    
    result = build_youtube_feed_url(channel_id)
    
    assert result == expected


def test_build_url_empty_raises() -> None:
    """Test that empty channel ID raises ValueError."""
    with pytest.raises(ValueError, match="channel_id cannot be empty"):
        build_youtube_feed_url("")
    
    with pytest.raises(ValueError, match="channel_id cannot be empty"):
        build_youtube_feed_url("   ")
    
    with pytest.raises(ValueError, match="channel_id cannot be empty"):
        build_youtube_feed_url("\t\n  ")


def test_build_url_non_string_raises() -> None:
    """Test that non-string channel ID raises ValueError."""
    with pytest.raises(ValueError, match="channel_id must be a string"):
        build_youtube_feed_url(123)  # type: ignore
    
    with pytest.raises(ValueError, match="channel_id must be a string"):
        build_youtube_feed_url(None)  # type: ignore
    
    with pytest.raises(ValueError, match="channel_id must be a string"):
        build_youtube_feed_url(["UC123"])  # type: ignore
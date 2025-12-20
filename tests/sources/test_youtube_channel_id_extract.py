"""Tests for YouTube channel ID extraction."""

import pytest

from tech_tracker.sources.youtube.channel import extract_channel_id_from_youtube_url


def test_extract_channel_id_normal_cases() -> None:
    """Test extracting channel ID from normal YouTube URLs."""
    # Test with www.youtube.com
    url = "https://www.youtube.com/channel/UC1234567890"
    assert extract_channel_id_from_youtube_url(url) == "UC1234567890"
    
    # Test with youtube.com (no www)
    url = "https://youtube.com/channel/UC1234567890"
    assert extract_channel_id_from_youtube_url(url) == "UC1234567890"
    
    # Test with trailing slash
    url = "https://www.youtube.com/channel/UC1234567890/"
    assert extract_channel_id_from_youtube_url(url) == "UC1234567890"
    
    # Test with youtube.com and trailing slash
    url = "https://youtube.com/channel/UC1234567890/"
    assert extract_channel_id_from_youtube_url(url) == "UC1234567890"


def test_extract_channel_id_with_query_params() -> None:
    """Test extracting channel ID with query parameters."""
    url = "https://www.youtube.com/channel/UC1234567890?sub_confirmation=1"
    assert extract_channel_id_from_youtube_url(url) == "UC1234567890"
    
    url = "https://youtube.com/channel/UC1234567890/?feature=share"
    assert extract_channel_id_from_youtube_url(url) == "UC1234567890"


def test_extract_channel_id_with_additional_path() -> None:
    """Test extracting channel ID with additional path components."""
    url = "https://www.youtube.com/channel/UC1234567890/videos"
    assert extract_channel_id_from_youtube_url(url) == "UC1234567890"
    
    url = "https://youtube.com/channel/UC1234567890/about"
    assert extract_channel_id_from_youtube_url(url) == "UC1234567890"


def test_extract_channel_id_with_leading_trailing_spaces() -> None:
    """Test extracting channel ID with leading/trailing spaces."""
    url = "  https://www.youtube.com/channel/UC1234567890  "
    assert extract_channel_id_from_youtube_url(url) == "UC1234567890"


def test_extract_channel_id_none_cases() -> None:
    """Test cases that should return None."""
    # Empty string
    assert extract_channel_id_from_youtube_url("") is None
    
    # Whitespace only
    assert extract_channel_id_from_youtube_url("   ") is None
    
    # Non-YouTube domain
    assert extract_channel_id_from_youtube_url("https://example.com/channel/UC123") is None
    
    # YouTube but not channel path
    assert extract_channel_id_from_youtube_url("https://www.youtube.com/user/someuser") is None
    
    # YouTube with handle (not supported in this task)
    assert extract_channel_id_from_youtube_url("https://www.youtube.com/@somehandle") is None
    
    # YouTube with custom URL
    assert extract_channel_id_from_youtube_url("https://www.youtube.com/c/customname") is None
    
    # YouTube short URL
    assert extract_channel_id_from_youtube_url("https://youtu.be/abc123") is None
    
    # YouTube homepage
    assert extract_channel_id_from_youtube_url("https://www.youtube.com/") is None
    
    # Malformed URL
    assert extract_channel_id_from_youtube_url("not-a-url") is None
    
    # URL without channel ID
    assert extract_channel_id_from_youtube_url("https://www.youtube.com/channel/") is None
    
    # Multiple slashes after channel
    assert extract_channel_id_from_youtube_url("https://www.youtube.com/channel//") is None


def test_extract_channel_id_various_schemes() -> None:
    """Test extracting channel ID with various URL schemes."""
    # HTTP
    url = "http://www.youtube.com/channel/UC1234567890"
    assert extract_channel_id_from_youtube_url(url) == "UC1234567890"
    
    # HTTPS
    url = "https://www.youtube.com/channel/UC1234567890"
    assert extract_channel_id_from_youtube_url(url) == "UC1234567890"
    
    # No scheme
    url = "www.youtube.com/channel/UC1234567890"
    # This might not parse correctly with urlparse, so we expect None
    assert extract_channel_id_from_youtube_url(url) is None


def test_extract_channel_id_complex_channel_ids() -> None:
    """Test extracting complex channel IDs."""
    # Channel ID with underscores and hyphens
    url = "https://www.youtube.com/channel/UC-Test_123-Channel_ID"
    assert extract_channel_id_from_youtube_url(url) == "UC-Test_123-Channel_ID"
    
    # Very long channel ID
    long_id = "UC" + "a" * 22  # YouTube channel IDs are typically 24 characters
    url = f"https://www.youtube.com/channel/{long_id}"
    assert extract_channel_id_from_youtube_url(url) == long_id
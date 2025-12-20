"""Tests for YouTube video fetching without network requests."""

from datetime import datetime, timezone

import pytest

from tech_tracker.downloader import FeedDownloader
from tech_tracker.youtube_fetch import fetch_youtube_videos
from tech_tracker.youtube_rss import build_youtube_feed_url


# Sample YouTube RSS feed XML with 2 entries (reused from test_youtube_rss_parse.py)
YOUTUBE_FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" 
      xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
  <id>yt:channel:UC1234567890</id>
  <title>Test Channel</title>
  <link rel="alternate" href="https://www.youtube.com/channel/UC1234567890"/>
  <updated>2023-12-20T10:00:00+00:00</updated>
  
  <entry>
    <yt:videoId>abc123def456</yt:videoId>
    <title>First Video Title</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123def456"/>
    <published>2023-12-20T09:00:00Z</published>
    <updated>2023-12-20T09:00:00Z</updated>
  </entry>
  
  <entry>
    <yt:videoId>xyz789uvw012</yt:videoId>
    <title>Second Video Title</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=xyz789uvw012"/>
    <published>2023-12-19T15:30:00Z</published>
    <updated>2023-12-19T15:30:00Z</updated>
  </entry>
</feed>"""


class FakeDownloader:
    """Fake downloader for testing without network requests."""
    
    def __init__(self, url_to_xml: dict[str, str]) -> None:
        """Initialize with a mapping of URLs to XML content.
        
        Args:
            url_to_xml: Dictionary mapping URLs to XML responses.
        """
        self.url_to_xml = url_to_xml
        self.fetched_urls = []  # Track which URLs were fetched
    
    def fetch_text(self, url: str) -> str:
        """Fetch text content from a URL.
        
        Args:
            url: The URL to fetch from.
            
        Returns:
            The XML content for the URL.
            
        Raises:
            ValueError: If the URL is not in the predefined mapping.
        """
        self.fetched_urls.append(url)
        
        if url not in self.url_to_xml:
            raise ValueError(f"Unknown URL: {url}")
        
        return self.url_to_xml[url]


def test_fetch_youtube_videos_with_fake_downloader() -> None:
    """Test fetching YouTube videos using FakeDownloader."""
    channel_id = "UC1234567890"
    expected_url = build_youtube_feed_url(channel_id)
    
    # Create fake downloader with our test XML
    fake_downloader = FakeDownloader({expected_url: YOUTUBE_FEED_XML})
    
    # Fetch videos
    videos = fetch_youtube_videos(channel_id, fake_downloader)
    
    # Verify results
    assert len(videos) == 2
    
    # Check first video
    first_video = videos[0]
    assert first_video["video_id"] == "abc123def456"
    assert first_video["title"] == "First Video Title"
    assert first_video["link"] == "https://www.youtube.com/watch?v=abc123def456"
    assert first_video["published"] == datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc)
    
    # Check second video
    second_video = videos[1]
    assert second_video["video_id"] == "xyz789uvw012"
    assert second_video["title"] == "Second Video Title"
    assert second_video["link"] == "https://www.youtube.com/watch?v=xyz789uvw012"
    assert second_video["published"] == datetime(2023, 12, 19, 15, 30, 0, tzinfo=timezone.utc)
    
    # Verify the correct URL was fetched
    assert len(fake_downloader.fetched_urls) == 1
    assert fake_downloader.fetched_urls[0] == expected_url


def test_fetch_youtube_videos_url_construction() -> None:
    """Test that the URL is constructed correctly."""
    channel_id = "  UCtest123  "  # With whitespace
    
    # Build expected URL
    expected_url = build_youtube_feed_url(channel_id)
    
    # Create fake downloader
    fake_downloader = FakeDownloader({expected_url: YOUTUBE_FEED_XML})
    
    # Fetch videos
    fetch_youtube_videos(channel_id, fake_downloader)
    
    # Verify the URL was fetched
    assert len(fake_downloader.fetched_urls) == 1
    assert fake_downloader.fetched_urls[0] == expected_url


def test_fetch_youtube_videos_empty_feed() -> None:
    """Test fetching videos from an empty feed."""
    channel_id = "UCempty123"
    expected_url = build_youtube_feed_url(channel_id)
    
    # Create fake downloader with empty feed
    empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" 
      xmlns="http://www.w3.org/2005/Atom">
  <id>yt:channel:UCempty123</id>
  <title>Empty Channel</title>
</feed>"""
    
    fake_downloader = FakeDownloader({expected_url: empty_xml})
    
    # Fetch videos
    videos = fetch_youtube_videos(channel_id, fake_downloader)
    
    # Verify results
    assert videos == []


def test_fetch_youtube_videos_downloader_error() -> None:
    """Test handling of downloader errors."""
    channel_id = "UCerror123"
    expected_url = build_youtube_feed_url(channel_id)
    
    # Create fake downloader that raises error
    fake_downloader = FakeDownloader({})
    
    # Fetch videos should raise ValueError
    with pytest.raises(ValueError, match="Unknown URL"):
        fetch_youtube_videos(channel_id, fake_downloader)


def test_fetch_youtube_videos_malformed_xml() -> None:
    """Test handling of malformed XML."""
    channel_id = "UCmalformed123"
    expected_url = build_youtube_feed_url(channel_id)
    
    # Create fake downloader with malformed XML
    malformed_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015">
  <unclosed_tag>
</feed>"""
    
    fake_downloader = FakeDownloader({expected_url: malformed_xml})
    
    # Fetch videos should raise ValueError
    with pytest.raises(ValueError, match="Failed to parse XML"):
        fetch_youtube_videos(channel_id, fake_downloader)
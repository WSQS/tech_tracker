"""Tests for YouTube app fetching from configuration."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from tech_tracker.app_youtube import fetch_youtube_videos_from_config
from tech_tracker.downloader import FeedDownloader
from tech_tracker.sources.youtube.rss import build_youtube_feed_url


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


def test_fetch_youtube_videos_from_config_normal(tmp_path: Path) -> None:
    """Test fetching YouTube videos from a normal configuration."""
    # Create test configuration
    config_content = """[[sources]]
type = "youtube"
url = "https://www.youtube.com/channel/UC1234567890"
title = "Test Channel"

[[sources]]
type = "youtube"
url = "https://www.youtube.com/@somehandle"
title = "Handle Channel"

[[sources]]
type = "rss"
url = "https://example.com/rss.xml"
title = "RSS Feed"

[[sources]]
type = "webpage"
url = "https://example.com"
title = "Web Page"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    
    # Build expected feed URL for the extractable channel
    expected_feed_url = build_youtube_feed_url("UC1234567890")
    
    # Create fake downloader
    fake_downloader = FakeDownloader({expected_feed_url: YOUTUBE_FEED_XML})
    
    # Fetch videos
    results = fetch_youtube_videos_from_config(config_file, fake_downloader)
    
    # Verify results
    assert len(results) == 1
    
    # Check that only the extractable YouTube source is included
    youtube_url = "https://www.youtube.com/channel/UC1234567890"
    assert youtube_url in results
    
    videos = results[youtube_url]
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
    
    # Verify the downloader was called exactly once with the expected URL
    assert len(fake_downloader.fetched_urls) == 1
    assert fake_downloader.fetched_urls[0] == expected_feed_url


def test_fetch_youtube_videos_from_config_multiple_extractable(tmp_path: Path) -> None:
    """Test fetching from multiple extractable YouTube sources."""
    # Create test configuration with multiple extractable channels
    config_content = """[[sources]]
type = "youtube"
url = "https://www.youtube.com/channel/UC1234567890"
title = "First Channel"

[[sources]]
type = "youtube"
url = "https://youtube.com/channel/UC0987654321/"
title = "Second Channel"

[[sources]]
type = "rss"
url = "https://example.com/rss.xml"
title = "RSS Feed"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    
    # Build expected feed URLs
    feed_url_1 = build_youtube_feed_url("UC1234567890")
    feed_url_2 = build_youtube_feed_url("UC0987654321")
    
    # Create fake downloader with different XML for each channel
    fake_downloader = FakeDownloader({
        feed_url_1: YOUTUBE_FEED_XML,
        feed_url_2: YOUTUBE_FEED_XML.replace("UC1234567890", "UC0987654321")
                          .replace("abc123def456", "uvw456xyz789")
                          .replace("xyz789uvw012", "stu012vwx345")
    })
    
    # Fetch videos
    results = fetch_youtube_videos_from_config(config_file, fake_downloader)
    
    # Verify results
    assert len(results) == 2
    
    # Check first channel
    url_1 = "https://www.youtube.com/channel/UC1234567890"
    assert url_1 in results
    assert len(results[url_1]) == 2
    assert results[url_1][0]["video_id"] == "abc123def456"
    
    # Check second channel
    url_2 = "https://youtube.com/channel/UC0987654321/"
    assert url_2 in results
    assert len(results[url_2]) == 2
    assert results[url_2][0]["video_id"] == "uvw456xyz789"
    
    # Verify the downloader was called twice
    assert len(fake_downloader.fetched_urls) == 2
    assert feed_url_1 in fake_downloader.fetched_urls
    assert feed_url_2 in fake_downloader.fetched_urls


def test_fetch_youtube_videos_from_config_no_extractable(tmp_path: Path) -> None:
    """Test configuration with no extractable YouTube sources."""
    # Create test configuration with no extractable channels
    config_content = """[[sources]]
type = "youtube"
url = "https://www.youtube.com/@somehandle"
title = "Handle Channel"

[[sources]]
type = "youtube"
url = "https://www.youtube.com/user/someuser"
title = "User Channel"

[[sources]]
type = "rss"
url = "https://example.com/rss.xml"
title = "RSS Feed"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    
    # Create fake downloader (should not be called)
    fake_downloader = FakeDownloader({})
    
    # Fetch videos
    results = fetch_youtube_videos_from_config(config_file, fake_downloader)
    
    # Verify no results
    assert results == {}
    
    # Verify the downloader was never called
    assert len(fake_downloader.fetched_urls) == 0


def test_fetch_youtube_videos_from_config_empty_config(tmp_path: Path) -> None:
    """Test with empty configuration."""
    # Create empty configuration
    config_content = """sources = []"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    
    # Create fake downloader (should not be called)
    fake_downloader = FakeDownloader({})
    
    # Fetch videos
    results = fetch_youtube_videos_from_config(config_file, fake_downloader)
    
    # Verify no results
    assert results == {}
    
    # Verify the downloader was never called
    assert len(fake_downloader.fetched_urls) == 0


def test_fetch_youtube_videos_from_config_downloader_error(tmp_path: Path) -> None:
    """Test handling of downloader errors."""
    # Create test configuration
    config_content = """[[sources]]
type = "youtube"
url = "https://www.youtube.com/channel/UC1234567890"
title = "Test Channel"

[[sources]]
type = "youtube"
url = "https://www.youtube.com/channel/UC0987654321"
title = "Error Channel"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    
    # Build expected feed URLs
    feed_url_1 = build_youtube_feed_url("UC1234567890")
    feed_url_2 = build_youtube_feed_url("UC0987654321")
    
    # Create fake downloader that fails for the second URL
    fake_downloader = FakeDownloader({feed_url_1: YOUTUBE_FEED_XML})
    # Note: feed_url_2 is not in the mapping, so it will raise an error
    
    # Fetch videos
    results = fetch_youtube_videos_from_config(config_file, fake_downloader)
    
    # Verify only the successful channel is included
    assert len(results) == 1
    
    url_1 = "https://www.youtube.com/channel/UC1234567890"
    assert url_1 in results
    assert len(results[url_1]) == 2
    
    # The error channel should not be in results
    url_2 = "https://www.youtube.com/channel/UC0987654321"
    assert url_2 not in results
"""Tests for YouTube items persistence."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from tech_tracker.app_persist import fetch_and_persist_youtube_items
from tech_tracker.item_store import JsonItemStore
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
    
    def fetch_text(self, url: str) -> str:
        """Fetch text content from a URL.
        
        Args:
            url: The URL to fetch from.
            
        Returns:
            The XML content for the URL.
            
        Raises:
            ValueError: If the URL is not in the predefined mapping.
        """
        if url not in self.url_to_xml:
            raise ValueError(f"Unknown URL: {url}")
        
        return self.url_to_xml[url]


def test_fetch_and_persist_youtube_items_normal(tmp_path: Path) -> None:
    """Test normal fetch and persist workflow."""
    # Create test configuration
    config_content = """[[sources]]
type = "youtube"
url = "https://www.youtube.com/channel/UC1234567890"
title = "Test Channel"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    
    # Build expected feed URL
    expected_feed_url = build_youtube_feed_url("UC1234567890")
    
    # Create fake downloader
    fake_downloader = FakeDownloader({expected_feed_url: YOUTUBE_FEED_XML})
    
    # Create item store
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Fetch and persist items
    count = fetch_and_persist_youtube_items(config_file, fake_downloader, store)
    
    # Verify count
    assert count == 2
    
    # Load items from store
    items = store.load_all()
    
    # Verify items count
    assert len(items) == 2
    
    # Verify first item
    first_item = items[0]
    assert first_item["item_id"] == "abc123def456"
    assert first_item["source_type"] == "youtube"
    assert first_item["source_url"] == "https://www.youtube.com/channel/UC1234567890"
    assert first_item["title"] == "First Video Title"
    assert first_item["link"] == "https://www.youtube.com/watch?v=abc123def456"
    
    # Verify published is datetime and timezone-aware UTC
    published = first_item["published"]
    assert isinstance(published, datetime)
    assert published.tzinfo == timezone.utc
    assert published == datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc)
    
    # Verify second item
    second_item = items[1]
    assert second_item["item_id"] == "xyz789uvw012"
    assert second_item["source_type"] == "youtube"
    assert second_item["source_url"] == "https://www.youtube.com/channel/UC1234567890"
    assert second_item["title"] == "Second Video Title"
    assert second_item["link"] == "https://www.youtube.com/watch?v=xyz789uvw012"
    
    # Verify published is datetime and timezone-aware UTC
    published = second_item["published"]
    assert isinstance(published, datetime)
    assert published.tzinfo == timezone.utc
    assert published == datetime(2023, 12, 19, 15, 30, 0, tzinfo=timezone.utc)


def test_fetch_and_persist_youtube_items_no_extractable(tmp_path: Path) -> None:
    """Test fetch and persist with no extractable sources."""
    # Create test configuration with no extractable channels
    config_content = """[[sources]]
type = "youtube"
url = "https://www.youtube.com/@somehandle"
title = "Handle Channel"

[[sources]]
type = "rss"
url = "https://example.com/rss.xml"
title = "RSS Feed"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    
    # Create fake downloader (should not be called)
    fake_downloader = FakeDownloader({})
    
    # Create item store
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Fetch and persist items
    count = fetch_and_persist_youtube_items(config_file, fake_downloader, store)
    
    # Verify count
    assert count == 0
    
    # Verify no items in store
    items = store.load_all()
    assert items == []


def test_fetch_and_persist_youtube_items_multiple_sources(tmp_path: Path) -> None:
    """Test fetch and persist with multiple YouTube sources."""
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
    
    # Create item store in a subdirectory to avoid conflicts
    store_path = tmp_path / "test_items" / "items.json"
    store = JsonItemStore(store_path)
    
    # Fetch and persist items
    count = fetch_and_persist_youtube_items(config_file, fake_downloader, store)
    
    # Verify count
    assert count == 4
    
    # Load items from store
    items = store.load_all()
    
    # Verify items count
    assert len(items) == 4
    
    # Verify items from first channel
    first_channel_items = [item for item in items if item["source_url"] == "https://www.youtube.com/channel/UC1234567890"]
    assert len(first_channel_items) == 2
    # Note: Items are sorted by published descending, then item_id ascending
    # Since both videos from the same channel have the same published time, they are sorted by item_id
    assert first_channel_items[0]["item_id"] == "abc123def456"
    assert first_channel_items[1]["item_id"] == "xyz789uvw012"
    
    # Verify items from second channel
    second_channel_items = [item for item in items if item["source_url"] == "https://youtube.com/channel/UC0987654321/"]
    assert len(second_channel_items) == 2
    assert second_channel_items[0]["item_id"] == "uvw456xyz789"
    assert second_channel_items[1]["item_id"] == "stu012vwx345"


def test_fetch_and_persist_youtube_items_with_existing_items(tmp_path: Path) -> None:
    """Test fetch and persist with existing items in store."""
    # Create test configuration
    config_content = """[[sources]]
type = "youtube"
url = "https://www.youtube.com/channel/UC1234567890"
title = "Test Channel"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    
    # Build expected feed URL
    expected_feed_url = build_youtube_feed_url("UC1234567890")
    
    # Create fake downloader
    fake_downloader = FakeDownloader({expected_feed_url: YOUTUBE_FEED_XML})
    
    # Create item store in a subdirectory to avoid conflicts
    store_path = tmp_path / "test_items" / "items.json"
    store = JsonItemStore(store_path)
    
    # Add existing items to store
    now = datetime.now(timezone.utc)
    existing_items = [
        {
            "item_id": "existing_item",
            "source_type": "rss",
            "source_url": "https://example.com/rss.xml",
            "title": "Existing Item",
            "link": "https://example.com/item",
            "published": now.replace(hour=8),
        },
        {
            "item_id": "abc123def456",  # This ID will be overwritten
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC1234567890",
            "title": "Old Title",
            "link": "https://www.youtube.com/watch?v=old",
            "published": now.replace(hour=9),
        },
    ]
    store.save_many(existing_items)
    
    # Fetch and persist items
    count = fetch_and_persist_youtube_items(config_file, fake_downloader, store)
    
    # Verify count (only new items)
    assert count == 2
    
    # Load items from store
    items = store.load_all()
    
    # Verify total items count (existing + new - overwritten)
    assert len(items) == 3
    
    # Verify existing item is still there
    existing_item = next(item for item in items if item["item_id"] == "existing_item")
    assert existing_item["title"] == "Existing Item"
    
    # Verify overwritten item has new data
    overwritten_item = next(item for item in items if item["item_id"] == "abc123def456")
    assert overwritten_item["title"] == "First Video Title"
    assert overwritten_item["link"] == "https://www.youtube.com/watch?v=abc123def456"
    assert overwritten_item["published"] == datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc)


def test_fetch_and_persist_youtube_items_downloader_error(tmp_path: Path) -> None:
    """Test fetch and persist with downloader error."""
    # Create test configuration
    config_content = """[[sources]]
type = "youtube"
url = "https://www.youtube.com/channel/UC1234567890"
title = "Test Channel"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    
    # Create fake downloader that raises error
    class ErrorDownloader:
        def fetch_text(self, url: str) -> str:
            raise ValueError("Network error")
    
    error_downloader = ErrorDownloader()
    
    # Create item store in a subdirectory to avoid conflicts
    store_path = tmp_path / "test_items" / "items.json"
    store = JsonItemStore(store_path)
    
    # Fetch and persist items
    count = fetch_and_persist_youtube_items(config_file, error_downloader, store)
    
    # Verify count
    assert count == 0
    
    # Verify no items in store
    items = store.load_all()
    assert items == []
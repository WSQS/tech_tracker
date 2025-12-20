"""Tests for YouTube update tracking functionality."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from tech_tracker.app_update import fetch_youtube_new_items
from tech_tracker.item_store import JsonItemStore
from tech_tracker.sources.youtube.rss import build_youtube_feed_url


# Sample YouTube RSS feed XML with 2 entries
YOUTUBE_FEED_XML_2_ENTRIES = """<?xml version="1.0" encoding="UTF-8"?>
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

# Sample YouTube RSS feed XML with 3 entries (added one more)
YOUTUBE_FEED_XML_3_ENTRIES = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" 
      xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
  <id>yt:channel:UC1234567890</id>
  <title>Test Channel</title>
  <link rel="alternate" href="https://www.youtube.com/channel/UC1234567890"/>
  <updated>2023-12-20T11:00:00+00:00</updated>
  
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
  
  <entry>
    <yt:videoId>new789xyz456</yt:videoId>
    <title>Third Video Title</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=new789xyz456"/>
    <published>2023-12-20T11:00:00Z</published>
    <updated>2023-12-20T11:00:00Z</updated>
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


def test_fetch_youtube_new_items_first_run_store_empty(tmp_path: Path) -> None:
    """Test scenario a): store initially empty, returns 2 new items."""
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
    
    # Create fake downloader with 2 entries
    fake_downloader = FakeDownloader({expected_feed_url: YOUTUBE_FEED_XML_2_ENTRIES})
    
    # Create item store
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Verify store is initially empty
    assert store.load_all() == []
    
    # Fetch new items
    new_items = fetch_youtube_new_items(config_file, fake_downloader, store)
    
    # Verify returns 2 new items
    assert len(new_items) == 2
    new_item_ids = {item["item_id"] for item in new_items}
    assert new_item_ids == {"abc123def456", "xyz789uvw012"}
    
    # Verify store now contains 2 items
    stored_items = store.load_all()
    assert len(stored_items) == 2
    stored_item_ids = {item["item_id"] for item in stored_items}
    assert stored_item_ids == {"abc123def456", "xyz789uvw012"}


def test_fetch_youtube_new_items_second_run_same_xml(tmp_path: Path) -> None:
    """Test scenario b): second run with same XML, returns no new items."""
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
    
    # Create fake downloader with 2 entries
    fake_downloader = FakeDownloader({expected_feed_url: YOUTUBE_FEED_XML_2_ENTRIES})
    
    # Create item store
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # First run: populate store
    new_items_first = fetch_youtube_new_items(config_file, fake_downloader, store)
    assert len(new_items_first) == 2
    
    # Second run: same XML
    new_items_second = fetch_youtube_new_items(config_file, fake_downloader, store)
    
    # Verify returns no new items
    assert len(new_items_second) == 0
    assert new_items_second == []
    
    # Verify store still contains 2 items
    stored_items = store.load_all()
    assert len(stored_items) == 2
    stored_item_ids = {item["item_id"] for item in stored_items}
    assert stored_item_ids == {"abc123def456", "xyz789uvw012"}


def test_fetch_youtube_new_items_third_run_new_entry(tmp_path: Path) -> None:
    """Test scenario c): third run with new entry, returns only the new one."""
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
    
    # Create item store
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # First run: with 2 entries
    fake_downloader_2 = FakeDownloader({expected_feed_url: YOUTUBE_FEED_XML_2_ENTRIES})
    new_items_first = fetch_youtube_new_items(config_file, fake_downloader_2, store)
    assert len(new_items_first) == 2
    
    # Second run: with 3 entries (one new)
    fake_downloader_3 = FakeDownloader({expected_feed_url: YOUTUBE_FEED_XML_3_ENTRIES})
    new_items_second = fetch_youtube_new_items(config_file, fake_downloader_3, store)
    
    # Verify returns only the new item
    assert len(new_items_second) == 1
    assert new_items_second[0]["item_id"] == "new789xyz456"
    assert new_items_second[0]["title"] == "Third Video Title"
    
    # Verify store now contains 3 items total
    stored_items = store.load_all()
    assert len(stored_items) == 3
    stored_item_ids = {item["item_id"] for item in stored_items}
    assert stored_item_ids == {"abc123def456", "xyz789uvw012", "new789xyz456"}
    
    # Verify the new item is the latest (sorted by published time)
    latest_item = stored_items[0]  # First item should be latest
    assert latest_item["item_id"] == "new789xyz456"
    assert latest_item["published"] == datetime(2023, 12, 20, 11, 0, 0, tzinfo=timezone.utc)
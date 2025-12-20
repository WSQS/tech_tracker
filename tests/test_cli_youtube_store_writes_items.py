"""Tests for CLI YouTube --store argument writing items to store."""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from tech_tracker.cli import main
from tech_tracker.item_store import JsonItemStore
from tech_tracker.youtube_rss import build_youtube_feed_url


# Sample YouTube RSS feed XML
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
    <title>Test Video Title</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123def456"/>
    <published>2023-12-20T09:00:00Z</published>
    <updated>2023-12-20T09:00:00Z</updated>
  </entry>
</feed>"""


class FakeDownloader:
    """Fake downloader for testing without network requests."""
    
    def __init__(self, url_to_xml: dict[str, str]) -> None:
        """Initialize with a mapping of URLs to XML content."""
        self.url_to_xml = url_to_xml
    
    def fetch_text(self, url: str) -> str:
        """Fetch text content from a URL."""
        if url not in self.url_to_xml:
            raise ValueError(f"Unknown URL: {url}")
        return self.url_to_xml[url]


def test_cli_youtube_without_store_no_file_created(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test scenario a): CLI without --store doesn't create store file."""
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
    
    # Define store path (should not be created)
    store_path = tmp_path / "items.json"
    
    # Patch UrllibFeedDownloader and run CLI
    with patch("tech_tracker.cli.UrllibFeedDownloader", return_value=fake_downloader):
        # Run CLI without --store
        result = main(["youtube", "--config", str(config_file)])
        
        # Check return code
        assert result == 0
        
        # Verify store file was not created
        assert not store_path.exists()
        
        # Verify stdout still outputs videos JSON
        captured = capsys.readouterr()
        output_json = json.loads(captured.out)
        assert isinstance(output_json, dict)
        
        youtube_url = "https://www.youtube.com/channel/UC1234567890"
        assert youtube_url in output_json
        assert len(output_json[youtube_url]) == 1
        assert output_json[youtube_url][0]["video_id"] == "abc123def456"


def test_cli_youtube_with_store_creates_file_and_writes_items(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test scenario b): CLI with --store creates file and writes correct items."""
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
    
    # Define store path
    store_path = tmp_path / "items.json"
    
    # Patch UrllibFeedDownloader and run CLI
    with patch("tech_tracker.cli.UrllibFeedDownloader", return_value=fake_downloader):
        # Run CLI with --store
        result = main(["youtube", "--config", str(config_file), "--store", str(store_path)])
        
        # Check return code
        assert result == 0
        
        # Verify store file was created
        assert store_path.exists()
        
        # Load and verify store contents
        store = JsonItemStore(store_path)
        items = store.load_all()
        
        # Should have 1 item
        assert len(items) == 1
        
        item = items[0]
        
        # Verify item fields
        assert item["item_id"] == "abc123def456"  # video_id -> item_id
        assert item["source_type"] == "youtube"
        assert item["source_url"] == "https://www.youtube.com/channel/UC1234567890"
        assert item["title"] == "Test Video Title"
        assert item["link"] == "https://www.youtube.com/watch?v=abc123def456"
        
        # Verify published is datetime and timezone-aware UTC
        published = item["published"]
        assert isinstance(published, datetime)
        assert published.tzinfo == timezone.utc
        assert published == datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc)
        
        # Verify stdout still outputs videos JSON (not items)
        captured = capsys.readouterr()
        output_json = json.loads(captured.out)
        assert isinstance(output_json, dict)
        
        youtube_url = "https://www.youtube.com/channel/UC1234567890"
        assert youtube_url in output_json
        assert len(output_json[youtube_url]) == 1
        assert output_json[youtube_url][0]["video_id"] == "abc123def456"
        
        # Verify stdout structure is videos, not items
        assert "item_id" not in output_json[youtube_url][0]  # videos have video_id, not item_id
        assert "source_type" not in output_json[youtube_url][0]  # videos don't have source_type
"""Tests for CLI YouTube default store behavior."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tech_tracker.cli import main
from tech_tracker.sources.youtube.rss import build_youtube_feed_url


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


def test_cli_youtube_default_store_is_incremental(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that CLI uses default store and shows incremental behavior."""
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
    
    # Expected default store path
    expected_store_path = tmp_path / ".tech-tracker" / "items.json"
    
    # Patch Path.home and UrllibFeedDownloader
    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("tech_tracker.cli.UrllibFeedDownloader", return_value=fake_downloader):
        
        # First run - should output the new item
        result1 = main(["youtube", "--config", str(config_file)])
        assert result1 == 0
        
        captured1 = capsys.readouterr()
        output_json1 = json.loads(captured1.out)
        
        # Verify first run output contains the item
        youtube_url = "https://www.youtube.com/channel/UC1234567890"
        assert youtube_url in output_json1
        assert len(output_json1[youtube_url]) == 1
        assert output_json1[youtube_url][0]["item_id"] == "abc123def456"
        
        # Verify default store file was created
        assert expected_store_path.exists()
        
        # Second run - should output empty dict (no new items)
        result2 = main(["youtube", "--config", str(config_file)])
        assert result2 == 0
        
        captured2 = capsys.readouterr()
        output_json2 = json.loads(captured2.out)
        
        # When no new items, output must be strictly empty dict {}
        assert output_json2 == {}
        
        # Verify default store file still exists
        assert expected_store_path.exists()
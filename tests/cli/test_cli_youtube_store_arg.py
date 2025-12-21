"""Tests for CLI YouTube --store argument."""

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


def test_cli_youtube_without_store_arg(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test scenario a): CLI without --store argument uses default store and outputs items."""
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
    
    # Define expected default store path
    default_store_path = tmp_path / ".tech-tracker" / "items.json"
    
    # Patch Path.home and UrllibFeedDownloader
    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("tech_tracker.cli.UrllibFeedDownloader", return_value=fake_downloader):
        
        # Run CLI without --store
        result = main(["youtube", "--config", str(config_file)])
        
        # Check return code
        assert result == 0
        
        # Verify default store file was created
        assert default_store_path.exists()
        
        # Capture stdout
        captured = capsys.readouterr()
        
        # Parse and verify JSON structure
        output_json = json.loads(captured.out)
        assert isinstance(output_json, dict)
        
        # The output should use the original YouTube URL as key, and contain items
        youtube_url = "https://www.youtube.com/channel/UC1234567890"
        assert youtube_url in output_json
        assert len(output_json[youtube_url]) == 1
        assert output_json[youtube_url][0]["item_id"] == "abc123def456"  # items have item_id, not video_id
        assert output_json[youtube_url][0]["title"] == "Test Video Title"


def test_cli_youtube_with_store_arg(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test scenario b): CLI with --store argument outputs normal JSON."""
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
    
    # Create store path (won't be used in this implementation)
    store_path = tmp_path / "items.json"
    
    # Patch UrllibFeedDownloader and run CLI
    with patch("tech_tracker.cli.UrllibFeedDownloader", return_value=fake_downloader):
        # Run CLI with --store
        result = main(["youtube", "--config", str(config_file), "--store", str(store_path)])
        
        # Check return code
        assert result == 0
        
        # Capture stdout
        captured = capsys.readouterr()
        
        # Parse and verify JSON structure
        output_json = json.loads(captured.out)
        assert isinstance(output_json, dict)
        
        # The output should use the original YouTube URL as key, but contain items (not videos)
        youtube_url = "https://www.youtube.com/channel/UC1234567890"
        assert youtube_url in output_json
        assert len(output_json[youtube_url]) == 1
        assert output_json[youtube_url][0]["item_id"] == "abc123def456"  # items have item_id
        assert output_json[youtube_url][0]["title"] == "Test Video Title"


def test_cli_youtube_store_arg_output_consistency(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test scenario c): outputs with and without --store are both items format."""
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
    
    # Store path
    store_path = tmp_path / "items.json"
    
    # Define expected default store path
    default_store_path = tmp_path / ".tech-tracker" / "items.json"
    
    # Run CLI without --store (uses default store)
    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("tech_tracker.cli.UrllibFeedDownloader", return_value=fake_downloader):
        result_without_store = main(["youtube", "--config", str(config_file)])
        captured_without_store = capsys.readouterr()
        json_without_store = json.loads(captured_without_store.out)
    
    # Run CLI with --store (uses specified store)
    with patch("tech_tracker.cli.UrllibFeedDownloader", return_value=fake_downloader):
        result_with_store = main(["youtube", "--config", str(config_file), "--store", str(store_path)])
        captured_with_store = capsys.readouterr()
        json_with_store = json.loads(captured_with_store.out)
    
    # Verify both exit codes are 0
    assert result_without_store == 0
    assert result_with_store == 0
    
    # Both should contain items format (now both use store mode)
    assert isinstance(json_without_store, dict)
    assert isinstance(json_with_store, dict)
    
    youtube_url = "https://www.youtube.com/channel/UC1234567890"
    
    # Both should contain the YouTube URL
    assert youtube_url in json_without_store
    assert youtube_url in json_with_store
    
    # Both should contain items (not videos)
    assert len(json_without_store[youtube_url]) == 1
    assert json_without_store[youtube_url][0]["item_id"] == "abc123def456"
    
    assert len(json_with_store[youtube_url]) == 1
    assert json_with_store[youtube_url][0]["item_id"] == "abc123def456"
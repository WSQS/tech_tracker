"""Tests for YouTube CLI command."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tech_tracker.cli import main
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


def test_cli_youtube_normal(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test normal YouTube CLI execution with default store."""
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
        
        # Run CLI command (now uses default store)
        result = main(["youtube", "--config", str(config_file)])
        
        # Check return code
        assert result == 0
        
        # Verify default store file was created
        assert default_store_path.exists()
        
        # Capture stdout
        captured = capsys.readouterr()
        
        # Parse JSON output
        output_data = json.loads(captured.out)
        
        # Verify structure (now outputs items, not videos)
        assert len(output_data) == 1
        
        youtube_url = "https://www.youtube.com/channel/UC1234567890"
        assert youtube_url in output_data
        
        items = output_data[youtube_url]
        assert len(items) == 2
        
        # Check first item
        first_item = items[0]
        assert first_item["item_id"] == "abc123def456"  # items have item_id, not video_id
        assert first_item["title"] == "First Video Title"
        assert first_item["link"] == "https://www.youtube.com/watch?v=abc123def456"
        assert first_item["source_type"] == "youtube"
        assert first_item["source_url"] == "https://www.youtube.com/channel/UC1234567890"
        
        # Check published date is a string with 'Z' suffix
        published = first_item["published"]
        assert isinstance(published, str)
        assert published == "2023-12-20T09:00:00Z"
        
        # Check second item
        second_item = items[1]
        assert second_item["item_id"] == "xyz789uvw012"  # items have item_id, not video_id
        assert second_item["title"] == "Second Video Title"
        assert second_item["link"] == "https://www.youtube.com/watch?v=xyz789uvw012"
        assert second_item["source_type"] == "youtube"
        assert second_item["source_url"] == "https://www.youtube.com/channel/UC1234567890"
        
        # Check published date is a string with 'Z' suffix
        published = second_item["published"]
        assert isinstance(published, str)
        assert published == "2023-12-19T15:30:00Z"


def test_cli_youtube_missing_config(capsys: pytest.CaptureFixture[str]) -> None:
    """Test YouTube CLI with missing config argument."""
    # Run CLI command without --config
    # Note: argparse will call sys.exit(2) for missing required args
    # So we need to handle SystemExit
    try:
        result = main(["youtube"])
        # If we get here, the behavior has changed
        assert result == 1
    except SystemExit as e:
        # argparse exits with code 2 for argument errors
        assert e.code == 2
    
    # Note: We can't easily capture stderr when argparse exits directly


def test_cli_youtube_nonexistent_config(capsys: pytest.CaptureFixture[str]) -> None:
    """Test YouTube CLI with nonexistent config file."""
    # Run CLI command with nonexistent config
    result = main(["youtube", "--config", "nonexistent.toml"])
    
    # Check return code
    assert result == 1
    
    # Capture stderr
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_cli_youtube_invalid_config(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test YouTube CLI with invalid config file."""
    # Create invalid configuration
    config_content = """invalid toml content"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    
    # Run CLI command
    result = main(["youtube", "--config", str(config_file)])
    
    # Check return code
    assert result == 1
    
    # Capture stderr
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_cli_youtube_no_extractable_sources(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test YouTube CLI with no extractable sources."""
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
    
    # Patch UrllibFeedDownloader to use our fake downloader
    with patch("tech_tracker.cli.UrllibFeedDownloader", return_value=fake_downloader):
        # Run CLI command
        result = main(["youtube", "--config", str(config_file)])
        
        # Check return code
        assert result == 0
        
        # Capture stdout
        captured = capsys.readouterr()
        
        # Parse JSON output
        output_data = json.loads(captured.out)
        
        # Verify empty result
        assert output_data == {}


def test_cli_youtube_downloader_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test YouTube CLI with downloader error."""
    # Create test configuration
    config_content = """[[sources]]
type = "youtube"
url = "https://www.youtube.com/channel/UC1234567890"
title = "Test Channel"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    
    # Patch fetch_youtube_new_items to raise an error
    with patch("tech_tracker.cli.fetch_youtube_new_items", side_effect=ValueError("Network error")):
        # Run CLI command
        result = main(["youtube", "--config", str(config_file)])
        
        # Check return code - should be 1 due to error
        assert result == 1
        
        # Capture stderr
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "Network error" in captured.err


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI help output."""
    # Run CLI command with --help
    # Note: argparse will call sys.exit(0) for help
    try:
        result = main(["--help"])
        # If we get here, the behavior has changed
        assert result == 0
    except SystemExit as e:
        # argparse exits with code 0 for help
        assert e.code == 0
    
    # Note: We can't easily capture stdout when argparse exits directly


def test_cli_youtube_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Test YouTube CLI help output."""
    # Run CLI command with youtube --help
    # Note: argparse will call sys.exit(0) for help
    try:
        result = main(["youtube", "--help"])
        # If we get here, the behavior has changed
        assert result == 0
    except SystemExit as e:
        # argparse exits with code 0 for help
        assert e.code == 0
    
    # Note: We can't easily capture stdout when argparse exits directly
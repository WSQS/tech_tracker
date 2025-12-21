"""Tests for CLI fetch command with default config path."""

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


def test_cli_fetch_uses_default_config_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that fetch command uses default config path when --config not provided."""
    # Create default config file in tmp_path's home directory
    default_config_path = tmp_path / ".config" / "tech-tracker" / "config.toml"
    default_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create test configuration
    config_content = """[[sources]]
type = "youtube"
url = "https://www.youtube.com/channel/UC1234567890"
title = "Test Channel"
"""
    default_config_path.write_text(config_content)
    
    # Build expected feed URL
    expected_feed_url = build_youtube_feed_url("UC1234567890")
    
    # Create fake downloader
    fake_downloader = FakeDownloader({expected_feed_url: YOUTUBE_FEED_XML})
    
    # Define expected default store path
    default_store_path = tmp_path / ".tech-tracker" / "items.json"
    
    # Patch Path.home and UrllibFeedDownloader
    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("tech_tracker.cli.UrllibFeedDownloader", return_value=fake_downloader):
        
        # Run CLI fetch command without --config
        result = main(["fetch"])
        
        # Check return code
        assert result == 0
        
        # Capture stdout
        captured = capsys.readouterr()
        
        # Should not contain "Created default config" message since config already exists
        assert "Created default config" not in captured.out
        
        # Parse and verify JSON structure
        output_json = json.loads(captured.out)
        assert isinstance(output_json, dict)
        
        # The output should use the original YouTube URL as key, and contain items
        youtube_url = "https://www.youtube.com/channel/UC1234567890"
        assert youtube_url in output_json
        assert len(output_json[youtube_url]) == 1
        assert output_json[youtube_url][0]["item_id"] == "abc123def456"
        assert output_json[youtube_url][0]["title"] == "Test Video Title"


def test_cli_fetch_creates_default_config_when_missing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that fetch command creates empty default config file when it doesn't exist."""
    # Ensure default config path doesn't exist initially
    default_config_path = tmp_path / ".config" / "tech-tracker" / "config.toml"
    assert not default_config_path.exists()
    assert not default_config_path.parent.exists()
    
    # Create fake downloader
    fake_downloader = FakeDownloader({})
    
    # Patch Path.home and UrllibFeedDownloader
    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("tech_tracker.cli.UrllibFeedDownloader", return_value=fake_downloader):
        
        # Run CLI fetch command without --config
        result = main(["fetch"])
        
        # Command will fail due to empty config, but config file should be created
        assert result == 1  # Expected to fail with empty config
        
        # Capture stdout and stderr
        captured = capsys.readouterr()
        
        # Verify default config creation message
        assert "Created default config" in captured.out
        assert str(default_config_path) in captured.out
        
        # Verify config file was created
        assert default_config_path.exists()
        assert default_config_path.parent.exists()
        
        # Verify config file is empty
        assert default_config_path.read_text(encoding="utf-8") == ""


def test_cli_fetch_missing_config_uses_default(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test fetch CLI with missing config argument (now uses default config instead of error)."""
    # This test covers the behavior that was previously tested in test_cli_fetch_missing_config
    # Before T004: missing --config would cause SystemExit with code 2
    # After T004: missing --config uses default config path and creates empty file if needed
    
    # Ensure default config path doesn't exist initially
    default_config_path = tmp_path / ".config" / "tech-tracker" / "config.toml"
    assert not default_config_path.exists()
    
    # Patch Path.home to use tmp_path
    with patch("pathlib.Path.home", return_value=tmp_path):
        # Run CLI command without --config (now uses default config instead of error)
        result = main(["fetch"])
        
        # Command should NOT exit with SystemExit, but return 1 due to empty config
        assert result == 1  # Expected to fail with empty config
        
        # Capture stdout and stderr
        captured = capsys.readouterr()
        
        # Verify default config creation message
        assert "Created default config" in captured.out
        assert str(default_config_path) in captured.out
        
        # Verify config file was created
        assert default_config_path.exists()
        assert default_config_path.parent.exists()
        
        # Verify config file is empty
        assert default_config_path.read_text(encoding="utf-8") == ""


def test_cli_fetch_explicit_config_overrides_default(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that explicit --config path overrides default config behavior."""
    # Create custom config file
    custom_config_path = tmp_path / "custom.toml"
    config_content = """[[sources]]
type = "youtube"
url = "https://www.youtube.com/channel/UC1234567890"
title = "Test Channel"
"""
    custom_config_path.write_text(config_content)
    
    # Ensure default config path doesn't exist
    default_config_path = tmp_path / ".config" / "tech-tracker" / "config.toml"
    assert not default_config_path.exists()
    assert not default_config_path.parent.exists()
    
    # Build expected feed URL
    expected_feed_url = build_youtube_feed_url("UC1234567890")
    
    # Create fake downloader
    fake_downloader = FakeDownloader({expected_feed_url: YOUTUBE_FEED_XML})
    
    # Define expected default store path
    default_store_path = tmp_path / ".tech-tracker" / "items.json"
    
    # Patch Path.home and UrllibFeedDownloader
    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("tech_tracker.cli.UrllibFeedDownloader", return_value=fake_downloader):
        
        # Run CLI fetch command with explicit --config
        result = main(["fetch", "--config", str(custom_config_path)])
        
        # Check return code
        assert result == 0
        
        # Capture stdout
        captured = capsys.readouterr()
        
        # Should not contain "Created default config" message
        assert "Created default config" not in captured.out
        
        # Verify default config was NOT created
        assert not default_config_path.exists()
        assert not default_config_path.parent.exists()
        
        # Parse and verify JSON structure
        output_json = json.loads(captured.out)
        assert isinstance(output_json, dict)
        
        # The output should use the original YouTube URL as key, and contain items
        youtube_url = "https://www.youtube.com/channel/UC1234567890"
        assert youtube_url in output_json
        assert len(output_json[youtube_url]) == 1
        assert output_json[youtube_url][0]["item_id"] == "abc123def456"
        assert output_json[youtube_url][0]["title"] == "Test Video Title"
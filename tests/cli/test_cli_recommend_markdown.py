"""Tests for CLI recommend command generating Markdown files."""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from tech_tracker.cli import main
from tech_tracker.item import Item
from tech_tracker.item_store import JsonItemStore


def test_cli_recommend_with_items(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI recommend command with items in store."""
    # Import recommender to test order directly
    from tech_tracker.app.recommend import LatestRecommender, RecommendRequest
    from tech_tracker.item_store import JsonItemStore
    
    # Create test items with proper tz-aware timestamps
    base_time = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="item1",
            source_type="youtube",
            source_url="https://youtube.com/channel/UC123",
            title="First Video",
            link="https://youtube.com/watch?v=abc123",
            published=base_time.replace(hour=12),  # Latest
        ),
        Item(
            item_id="item2",
            source_type="rss",
            source_url="https://example.com/rss.xml",
            title="Second Article",
            link="https://example.com/article1",
            published=base_time.replace(hour=10),  # Earlier
        ),
        Item(
            item_id="item3",
            source_type="youtube",
            source_url="https://youtube.com/channel/UC456",
            title="Third Video",
            link="https://youtube.com/watch?v=def456",
            published=base_time.replace(hour=11),  # Middle
        ),
    ]
    
    # Create store in tmp_path (acting as home directory)
    store_path = tmp_path / ".tech-tracker" / "items.json"
    store = JsonItemStore(store_path)
    store.save_many(items)
    
    # Create the same recommender that CLI uses
    recommender = LatestRecommender()
    req = RecommendRequest(items=items, limit=20)
    expected_result = recommender.recommend(req)
    
    # Expected output file path (CWD)
    output_file = tmp_path / "recommend.md"
    
    # Run CLI recommend command with tmp_path as CWD
    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("pathlib.Path.cwd", return_value=tmp_path):
        
        result = main(["recommend"])
        
        # Check return code
        assert result == 0
        
        # Capture stdout
        captured = capsys.readouterr()
        
        # Verify stdout contains only the write message, not the Markdown content
        assert "Written to" in captured.out
        assert "recommend.md" in captured.out
        assert "# Recommended Items" not in captured.out
        
        # Verify output file was created
        assert output_file.exists()
        
        # Read and verify Markdown content
        markdown_content = output_file.read_text(encoding="utf-8")
        
        # Verify Markdown structure contains header
        assert "# Recommended Items" in markdown_content
        
        # Extract titles from markdown and verify order matches recommender output
        title_lines = [line for line in markdown_content.split('\n') if line.startswith("## ")]
        
        # Extract item titles from recommender result in the same order
        expected_titles = [item.title for item in expected_result.items]
        
        # Extract titles from markdown, removing "## " prefix and numbering
        markdown_titles = []
        for line in title_lines[:len(expected_titles)]:
            title = line.replace("## ", "").replace("\r", "").replace("\n", "")
            # Remove numbering prefix if present (e.g., "1. ", "2. ", etc.)
            if ". " in title:
                title = title.split(". ", 1)[1]
            markdown_titles.append(title)
        
        # Verify both content existence and order: all expected titles must be present in correct order
        assert len(markdown_titles) == len(expected_titles)
        assert expected_titles == markdown_titles


def test_cli_recommend_with_empty_store(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI recommend command with empty store."""
    # Create empty store
    store_path = tmp_path / ".tech-tracker" / "items.json"
    store = JsonItemStore(store_path)
    # Store is empty by default
    
    # Expected output file path (CWD)
    output_file = tmp_path / "recommend.md"
    
    # Run CLI recommend command with tmp_path as CWD
    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("pathlib.Path.cwd", return_value=tmp_path):
        
        result = main(["recommend"])
        
        # Check return code
        assert result == 0
        
        # Capture stdout
        captured = capsys.readouterr()
        
        # Verify stdout contains only the write message
        assert "Written to" in captured.out
        assert "recommend.md" in captured.out
        assert "# Recommended Items" not in captured.out
        
        # Verify output file was created
        assert output_file.exists()
        
        # Read and verify Markdown content contains header even when empty
        markdown_content = output_file.read_text(encoding="utf-8")
        assert "# Recommended Items" in markdown_content
        
        # Should not contain any item sections
        assert "## " not in markdown_content or markdown_content.count("## ") == 0


def test_cli_recommend_overwrites_existing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI recommend command overwrites existing file."""
    # Create existing output file
    output_file = tmp_path / "recommend.md"
    output_file.write_text("Existing content that should be overwritten", encoding="utf-8")
    
    # Create test items
    base_time = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="item1",
            source_type="youtube",
            source_url="https://youtube.com/channel/UC123",
            title="New Video",
            link="https://youtube.com/watch?v=abc123",
            published=base_time,
        ),
    ]
    
    # Create store
    store_path = tmp_path / ".tech-tracker" / "items.json"
    store = JsonItemStore(store_path)
    store.save_many(items)
    
    # Run CLI recommend command with tmp_path as CWD
    with patch("pathlib.Path.home", return_value=tmp_path), \
         patch("pathlib.Path.cwd", return_value=tmp_path):
        
        result = main(["recommend"])
        
        # Check return code
        assert result == 0
        
        # Verify file was overwritten
        markdown_content = output_file.read_text(encoding="utf-8")
        assert "Existing content that should be overwritten" not in markdown_content
        assert "# Recommended Items" in markdown_content
        
        # Verify the expected title appears in markdown (without hardcoded numbering)
        assert "New Video" in markdown_content
        # Should contain a section with the video title
        title_lines = [line for line in markdown_content.split('\n') if line.startswith("## ")]
        assert any("New Video" in line for line in title_lines)
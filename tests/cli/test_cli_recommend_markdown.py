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
        
        # Verify Markdown structure
        assert "# Recommended Items" in markdown_content
        assert "## 1. First Video" in markdown_content
        assert "## 2. Third Video" in markdown_content
        assert "## 3. Second Article" in markdown_content
        
        # Verify order matches recommender output (latest first, then tie-break by item_id)
        lines = markdown_content.split('\n')
        
        # Find the order of titles
        title_lines = [line for line in lines if line.startswith("## ")]
        assert len(title_lines) >= 3
        
        # Verify the order is correct (First Video, Third Video, Second Article)
        assert "## 1. First Video" == title_lines[0]
        assert "## 2. Third Video" == title_lines[1] 
        assert "## 3. Second Article" == title_lines[2]


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
        assert "## 1. New Video" in markdown_content
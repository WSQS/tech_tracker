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
    """Test CLI recommend command with items in store (dual mode output)."""
    # Import recommenders to test order directly
    from tech_tracker.app.recommend import LatestRecommender, KeywordFromSeenRecommender, RecommendRequest
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
    
    # Create the same recommenders that CLI uses
    latest_recommender = LatestRecommender()
    keyword_recommender = KeywordFromSeenRecommender()
    req = RecommendRequest(items=items, limit=20)
    
    latest_result = latest_recommender.recommend(req)
    keyword_result = keyword_recommender.recommend(req)
    
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
        assert "## " not in captured.out
        
        # Verify output file was created
        assert output_file.exists()
        
        # Read and verify Markdown content
        markdown_content = output_file.read_text(encoding="utf-8")
        
        # Verify dual-mode structure
        assert "# Recommended Items" in markdown_content
        assert "## Latest" in markdown_content
        assert "## Keyword from Seen" in markdown_content
        
        # Verify section order
        latest_pos = markdown_content.find("## Latest")
        keyword_pos = markdown_content.find("## Keyword from Seen")
        assert latest_pos < keyword_pos
        
        # Verify content from both recommenders
        assert "item1" in markdown_content  # Should appear in Latest section
        assert "item2" in markdown_content  # Should appear in Latest section
        assert "item3" in markdown_content  # Should appear in Latest section
        
        # Verify that item sections are present in both sections
        item_sections = [line for line in markdown_content.split('\n') if line.startswith("## 1.")]
        assert len(item_sections) >= 1  # At least one item should be present
        
        # Verify that item_id lines are present and correctly formatted
        id_lines = [line for line in markdown_content.split('\n') if line.startswith("- ID:")]
        assert len(id_lines) >= 1  # At least one item ID should be present
        
        # Verify specific items are present
        assert "item1" in markdown_content
        assert "item2" in markdown_content
        assert "item3" in markdown_content


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
        assert "## " not in captured.out
        
        # Verify output file was created
        assert output_file.exists()
        
        # Read and verify Markdown content contains dual-mode structure when no items
        markdown_content = output_file.read_text(encoding="utf-8")
        
        # Should contain main title and both section titles
        assert "# Recommended Items" in markdown_content
        assert "## Latest" in markdown_content
        assert "## Keyword from Seen" in markdown_content
        
        # Should contain meta information from both recommenders
        assert "_Strategy_: latest" in markdown_content
        assert "_Limit_: 20" in markdown_content
        assert "_Strategy_: keyword_from_seen" in markdown_content
        
        # Should not contain any item sections (only section titles and meta)
        item_sections = [line for line in markdown_content.split('\n') if line.startswith("## 1.")]
        assert len(item_sections) == 0


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
        
        # Verify dual-mode structure
        assert "# Recommended Items" in markdown_content
        assert "## Latest" in markdown_content
        assert "## Keyword from Seen" in markdown_content
        
        # Verify the expected title appears in markdown (without hardcoded numbering)
        assert "New Video" in markdown_content
        # Should contain a section with the video title
        title_lines = [line for line in markdown_content.split('\n') if line.startswith("## 1.")]
        assert any("New Video" in line for line in title_lines)
        
        # Verify that the item_id is properly displayed in the markdown
        assert "ID: `item1`" in markdown_content
        # Should contain the ID line in the correct format with backticks
        id_lines = [line for line in markdown_content.split('\n') if line.startswith("- ID:")]
        assert any("`item1`" in line for line in id_lines)


def test_cli_recommend_dual_mode_structure(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI recommend command produces correct dual-mode structure."""
    # Create test items with seen/unseen to test both recommenders
    base_time = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="seen:python",
            source_type="youtube",
            source_url="https://youtube.com/channel/python",
            title="Python Programming Tutorial",
            link="https://youtube.com/watch?v=python123",
            published=base_time.replace(hour=10),
            seen=True
        ),
        Item(
            item_id="unseen:python",
            source_type="youtube", 
            source_url="https://youtube.com/channel/python",
            title="Advanced Python Guide",
            link="https://youtube.com/watch?v=python456",
            published=base_time.replace(hour=12),
            seen=False
        ),
        Item(
            item_id="unseen:javascript",
            source_type="youtube",
            source_url="https://youtube.com/channel/javascript",
            title="JavaScript Basics",
            link="https://youtube.com/watch?v=js789",
            published=base_time.replace(hour=11),
            seen=False
        ),
    ]
    
    # Create store
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
        
        # Verify output file was created
        assert output_file.exists()
        
        # Read and verify dual-mode structure
        markdown_content = output_file.read_text(encoding="utf-8")
        
        # 1) Verify main title exists and appears only once
        lines = markdown_content.split('\n')
        assert lines[0] == "# Recommended Items"
        assert lines.count("# Recommended Items") == 1
        
        # 2) Verify section titles exist in correct order
        assert "## Latest" in markdown_content
        assert "## Keyword from Seen" in markdown_content
        latest_pos = markdown_content.find("## Latest")
        keyword_pos = markdown_content.find("## Keyword from Seen")
        assert latest_pos < keyword_pos
        
        # 3) Verify each section contains expected content
        # Latest section should contain all unseen items (fallback behavior)
        assert "unseen:python" in markdown_content
        assert "unseen:javascript" in markdown_content
        assert "seen:python" in markdown_content  # Seen item appears in Latest fallback
        
        # Keyword section should contain only items matching seen keywords
        assert "unseen:python" in markdown_content  # Matches "python" from seen item
        # Note: "unseen:javascript" may or may not appear depending on keyword matching
        # "seen:python" should NOT appear in Keyword section
        
        # 4) Verify meta information from both recommenders
        assert "_Strategy_: latest" in markdown_content
        assert "_Strategy_: keyword_from_seen" in markdown_content
        
        # 5) Verify item sections are properly formatted
        item_sections = [line for line in markdown_content.split('\n') if line.startswith("## 1.")]
        assert len(item_sections) >= 1  # At least one item should be present
        
        # 6) Verify proper section separation
        latest_section_end = markdown_content.find("## Keyword from Seen")
        latest_section_content = markdown_content[:latest_section_end]
        keyword_section_content = markdown_content[keyword_pos:]
        
        # Each section should have its own content
        assert "unseen:python" in latest_section_content
        assert "unseen:python" in keyword_section_content
"""Tests for CLI import command."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tech_tracker.cli import main
from tech_tracker.item import Item
from tech_tracker.item_store import JsonItemStore


def create_test_store_with_items(store_path: Path, items_data: list[dict]) -> None:
    """Create a test store with the given items.
    
    Args:
        store_path: Path to the store file.
        items_data: List of item dictionaries.
    """
    # Convert dictionaries to Item objects
    items = []
    for item_dict in items_data:
        # Convert published string to datetime if needed
        if isinstance(item_dict["published"], str):
            published_str = item_dict["published"]
            if not published_str.endswith("Z"):
                raise ValueError("Published datetime must end with 'Z'")
            published_str = published_str[:-1] + "+00:00"
            published = datetime.fromisoformat(published_str)
        else:
            published = item_dict["published"]
        
        item = Item(
            item_id=item_dict["item_id"],
            source_type=item_dict["source_type"],
            source_url=item_dict["source_url"],
            title=item_dict["title"],
            link=item_dict["link"],
            published=published,
            seen=item_dict.get("seen", False),
        )
        items.append(item)
    
    # Save to store
    store = JsonItemStore(store_path)
    store.save_many(items)


def test_cli_import_normal_case() -> None:
    """Test normal import: empty store + 2 items -> store gets 2 items."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create input file with 2 items
        input_file = temp_path / "input.json"
        input_data = {
            "items": [
                {
                    "item_id": "test:item1",
                    "source_type": "test",
                    "source_url": "https://example.com/source1",
                    "title": "Test Item 1",
                    "link": "https://example.com/item1",
                    "published": "2023-12-20T10:00:00Z",
                    "seen": False
                },
                {
                    "item_id": "test:item2",
                    "source_type": "test",
                    "source_url": "https://example.com/source2",
                    "title": "Test Item 2",
                    "link": "https://example.com/item2",
                    "published": "2023-12-19T15:30:00Z",
                    "seen": True
                }
            ]
        }
        input_file.write_text(json.dumps(input_data), encoding="utf-8")
        
        # Create empty store
        store_file = temp_path / "store.json"
        
        # Run import command
        result = main(["import", str(input_file), "--store", str(store_file)])
        
        # Verify exit code
        assert result == 0
        
        # Verify store content
        store = JsonItemStore(store_file)
        items = store.load_all()
        assert len(items) == 2
        
        # Verify items are sorted by published desc
        items_sorted = sorted(items, key=lambda x: (-x.published.timestamp(), x.item_id))
        assert items == items_sorted
        
        # Verify item content
        item_ids = {item.item_id for item in items}
        assert item_ids == {"test:item1", "test:item2"}


def test_cli_import_duplicate_ignoring() -> None:
    """Test duplicate ignoring: store has 1 item + input has that item + new item -> only 1 new item added."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create store with 1 existing item
        store_file = temp_path / "store.json"
        existing_item = {
            "item_id": "test:existing",
            "source_type": "test",
            "source_url": "https://example.com/source",
            "title": "Existing Item",
            "link": "https://example.com/existing",
            "published": "2023-12-18T10:00:00Z",
            "seen": True
        }
        create_test_store_with_items(store_file, [existing_item])
        
        # Create input file with existing item + new item
        input_file = temp_path / "input.json"
        input_data = {
            "items": [
                existing_item,  # This should be ignored
                {
                    "item_id": "test:new",
                    "source_type": "test",
                    "source_url": "https://example.com/source2",
                    "title": "New Item",
                    "link": "https://example.com/new",
                    "published": "2023-12-20T10:00:00Z",
                    "seen": False
                }
            ]
        }
        input_file.write_text(json.dumps(input_data), encoding="utf-8")
        
        # Run import command
        result = main(["import", str(input_file), "--store", str(store_file)])
        
        # Verify exit code
        assert result == 0
        
        # Verify store content
        store = JsonItemStore(store_file)
        items = store.load_all()
        assert len(items) == 2
        
        # Verify item IDs
        item_ids = {item.item_id for item in items}
        assert item_ids == {"test:existing", "test:new"}


def test_cli_import_single_dict() -> None:
    """Test importing a single item dict (not in items array)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create input file with single item dict
        input_file = temp_path / "input.json"
        input_data = {
            "item_id": "test:single",
            "source_type": "test",
            "source_url": "https://example.com/source",
            "title": "Single Item",
            "link": "https://example.com/single",
            "published": "2023-12-20T10:00:00Z",
            "seen": False
        }
        input_file.write_text(json.dumps(input_data), encoding="utf-8")
        
        # Create empty store
        store_file = temp_path / "store.json"
        
        # Run import command
        result = main(["import", str(input_file), "--store", str(store_file)])
        
        # Verify exit code
        assert result == 0
        
        # Verify store content
        store = JsonItemStore(store_file)
        items = store.load_all()
        assert len(items) == 1
        assert items[0].item_id == "test:single"


def test_cli_import_invalid_json() -> None:
    """Test handling of invalid JSON input."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create input file with invalid JSON
        input_file = temp_path / "input.json"
        input_file.write_text("{ invalid json", encoding="utf-8")
        
        # Create empty store
        store_file = temp_path / "store.json"
        
        # Run import command
        result = main(["import", str(input_file), "--store", str(store_file)])
        
        # Verify exit code is non-zero
        assert result != 0


def test_cli_import_invalid_structure() -> None:
    """Test handling of invalid input structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create input file with invalid structure (string instead of dict/array)
        input_file = temp_path / "input.json"
        input_file.write_text('"invalid structure"', encoding="utf-8")
        
        # Create empty store
        store_file = temp_path / "store.json"
        
        # Run import command
        result = main(["import", str(input_file), "--store", str(store_file)])
        
        # Verify exit code is non-zero
        assert result != 0


def test_cli_import_invalid_item_data() -> None:
    """Test handling of invalid item data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create input file with missing required fields
        input_file = temp_path / "input.json"
        input_data = {
            "items": [
                {
                    "item_id": "test:incomplete",
                    # Missing required fields
                }
            ]
        }
        input_file.write_text(json.dumps(input_data), encoding="utf-8")
        
        # Create empty store
        store_file = temp_path / "store.json"
        
        # Run import command
        result = main(["import", str(input_file), "--store", str(store_file)])
        
        # Verify exit code is non-zero
        assert result != 0


def test_cli_import_nonexistent_file() -> None:
    """Test handling of nonexistent input file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create empty store
        store_file = temp_path / "store.json"
        
        # Run import command with nonexistent file
        result = main(["import", "nonexistent.json", "--store", str(store_file)])
        
        # Verify exit code is non-zero
        assert result != 0


def test_cli_import_empty_items() -> None:
    """Test handling of empty items list."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create input file with empty items array
        input_file = temp_path / "input.json"
        input_data = {"items": []}
        input_file.write_text(json.dumps(input_data), encoding="utf-8")
        
        # Create empty store
        store_file = temp_path / "store.json"
        
        # Run import command
        result = main(["import", str(input_file), "--store", str(store_file)])
        
        # Verify exit code is 0 (success)
        assert result == 0
        
        # Verify store remains empty
        store = JsonItemStore(store_file)
        items = store.load_all()
        assert len(items) == 0
"""Tests for CLI modify command."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

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


def test_cli_modify_seen_success(tmp_path: Path) -> None:
    """Test marking an item as seen successfully."""
    # Create test store with items
    store_path = tmp_path / "test_store.json"
    test_items = [
        {
            "item_id": "test123",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Test Video",
            "link": "https://www.youtube.com/watch?v=test123",
            "published": "2023-12-20T09:00:00Z",
            "seen": False,
        }
    ]
    create_test_store_with_items(store_path, test_items)
    
    # Run CLI command to mark item as seen
    exit_code = main(["modify", "--store", str(store_path), "seen", "test123"])
    
    # Verify command succeeded
    assert exit_code == 0
    
    # Load store and verify item is now seen
    store = JsonItemStore(store_path)
    items = store.load_all()
    assert len(items) == 1
    
    item = items[0]
    assert item.item_id == "test123"
    assert item.seen is True


def test_cli_modify_unseen_success(tmp_path: Path) -> None:
    """Test marking an item as unseen successfully."""
    # Create test store with items (already seen)
    store_path = tmp_path / "test_store.json"
    test_items = [
        {
            "item_id": "test456",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Test Video 2",
            "link": "https://www.youtube.com/watch?v=test456",
            "published": "2023-12-20T10:00:00Z",
            "seen": True,
        }
    ]
    create_test_store_with_items(store_path, test_items)
    
    # Run CLI command to mark item as unseen
    exit_code = main(["modify", "--store", str(store_path), "unseen", "test456"])
    
    # Verify command succeeded
    assert exit_code == 0
    
    # Load store and verify item is now unseen
    store = JsonItemStore(store_path)
    items = store.load_all()
    assert len(items) == 1
    
    item = items[0]
    assert item.item_id == "test456"
    assert item.seen is False


def test_cli_modify_item_not_found(tmp_path: Path) -> None:
    """Test error when trying to modify a non-existent item."""
    # Create test store with items
    store_path = tmp_path / "test_store.json"
    test_items = [
        {
            "item_id": "existing123",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Existing Video",
            "link": "https://www.youtube.com/watch?v=existing123",
            "published": "2023-12-20T09:00:00Z",
            "seen": False,
        }
    ]
    create_test_store_with_items(store_path, test_items)
    
    # Run CLI command to mark non-existent item as seen
    exit_code = main(["modify", "--store", str(store_path), "seen", "nonexistent456"])
    
    # Verify command failed
    assert exit_code == 1
    
    # Load store and verify nothing changed
    store = JsonItemStore(store_path)
    items = store.load_all()
    assert len(items) == 1
    
    item = items[0]
    assert item.item_id == "existing123"
    assert item.seen is False


def test_cli_modify_with_default_store(tmp_path: Path, monkeypatch) -> None:
    """Test modify command with default store path."""
    # Mock the default store path to use our temp directory
    default_store_path = tmp_path / ".tech-tracker" / "items.json"
    monkeypatch.setattr("tech_tracker.cli.default_store_path", lambda: default_store_path)
    
    # Create test store with items
    test_items = [
        {
            "item_id": "default123",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Default Store Video",
            "link": "https://www.youtube.com/watch?v=default123",
            "published": "2023-12-20T09:00:00Z",
            "seen": False,
        }
    ]
    create_test_store_with_items(default_store_path, test_items)
    
    # Run CLI command without --store argument
    exit_code = main(["modify", "seen", "default123"])
    
    # Verify command succeeded
    assert exit_code == 0
    
    # Load store and verify item is now seen
    store = JsonItemStore(default_store_path)
    items = store.load_all()
    assert len(items) == 1
    
    item = items[0]
    assert item.item_id == "default123"
    assert item.seen is True


def test_cli_modify_preserves_other_fields(tmp_path: Path) -> None:
    """Test that modify command preserves all other item fields."""
    # Create test store with items
    store_path = tmp_path / "test_store.json"
    original_published = datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc)
    test_items = [
        {
            "item_id": "preserve123",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Original Title",
            "link": "https://www.youtube.com/watch?v=preserve123",
            "published": original_published,
            "seen": False,
        }
    ]
    create_test_store_with_items(store_path, test_items)
    
    # Run CLI command to mark item as seen
    exit_code = main(["modify", "--store", str(store_path), "seen", "preserve123"])
    
    # Verify command succeeded
    assert exit_code == 0
    
    # Load store and verify all fields are preserved except seen status
    store = JsonItemStore(store_path)
    items = store.load_all()
    assert len(items) == 1
    
    item = items[0]
    assert item.item_id == "preserve123"
    assert item.source_type == "youtube"
    assert item.source_url == "https://www.youtube.com/channel/UC123"
    assert item.title == "Original Title"
    assert item.link == "https://www.youtube.com/watch?v=preserve123"
    assert item.published == original_published
    assert item.seen is True  # Only this field should change


def test_cli_modify_empty_store(tmp_path: Path) -> None:
    """Test modify command with empty store."""
    # Create empty test store
    store_path = tmp_path / "empty_store.json"
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps({"items": []}), encoding="utf-8")
    
    # Run CLI command to mark non-existent item as seen
    exit_code = main(["modify", "--store", str(store_path), "seen", "nonexistent123"])
    
    # Verify command failed
    assert exit_code == 1
    
    # Load store and verify it's still empty
    store = JsonItemStore(store_path)
    items = store.load_all()
    assert len(items) == 0


def test_cli_modify_nonexistent_store(tmp_path: Path) -> None:
    """Test modify command with non-existent store file."""
    # Path to non-existent store
    store_path = tmp_path / "nonexistent_store.json"
    
    # Run CLI command to mark item as seen
    exit_code = main(["modify", "--store", str(store_path), "seen", "test123"])
    
    # Verify command failed
    assert exit_code == 1
    
    # Verify store file was not created
    assert not store_path.exists()


def test_cli_modify_help() -> None:
    """Test that modify help commands work without errors."""
    import pytest
    
    # Test modify help
    with pytest.raises(SystemExit) as excinfo:
        main(["modify", "--help"])
    assert excinfo.value.code == 0
    
    # Test seen help
    with pytest.raises(SystemExit) as excinfo:
        main(["modify", "seen", "--help"])
    assert excinfo.value.code == 0
    
    # Test unseen help
    with pytest.raises(SystemExit) as excinfo:
        main(["modify", "unseen", "--help"])
    assert excinfo.value.code == 0
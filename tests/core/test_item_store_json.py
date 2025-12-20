"""Tests for JSON item store."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest

from tech_tracker.item_store import JsonItemStore
from tech_tracker.item import Item


def dict_to_item(item_dict: Dict[str, Any]) -> Item:
    """Convert dictionary to Item object."""
    return Item(
        item_id=item_dict["item_id"],
        source_type=item_dict["source_type"],
        source_url=item_dict["source_url"],
        title=item_dict["title"],
        link=item_dict["link"],
        published=item_dict["published"],
    )


def test_load_all_nonexistent_file(tmp_path: Path) -> None:
    """Test loading from a nonexistent file returns empty list."""
    store_path = tmp_path / "nonexistent.json"
    store = JsonItemStore(store_path)
    
    items = store.load_all()
    
    assert items == []


def test_save_and_load_items(tmp_path: Path) -> None:
    """Test saving and loading items."""
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Create test items
    now = datetime.now(timezone.utc)
    items = [
        {
            "item_id": "item1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "First Video",
            "link": "https://www.youtube.com/watch?v=abc123",
            "published": now,
        },
        {
            "item_id": "item2",
            "source_type": "rss",
            "source_url": "https://example.com/rss.xml",
            "title": "First Article",
            "link": "https://example.com/article1",
            "published": now.replace(hour=10),  # Different time
        },
    ]
    
    # Convert dicts to Item objects and save
    item_objects = [dict_to_item(item) for item in items]
    store.save_many(item_objects)
    
    # Load items
    loaded_items = store.load_all()
    
    # Verify items match
    assert len(loaded_items) == 2
    assert loaded_items[0].item_id == "item1"
    assert loaded_items[0].source_type == "youtube"
    assert loaded_items[0].title == "First Video"
    assert loaded_items[0].published == now
    
    assert loaded_items[1].item_id == "item2"
    assert loaded_items[1].source_type == "rss"
    assert loaded_items[1].title == "First Article"
    assert loaded_items[1].published == now.replace(hour=10)


def test_save_and_load_with_existing_items(tmp_path: Path) -> None:
    """Test saving items when file already contains items."""
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Create initial items
    now = datetime.now(timezone.utc)
    initial_items = [
        {
            "item_id": "item1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "First Video",
            "link": "https://www.youtube.com/watch?v=abc123",
            "published": now,
        },
        {
            "item_id": "item2",
            "source_type": "rss",
            "source_url": "https://example.com/rss.xml",
            "title": "First Article",
            "link": "https://example.com/article1",
            "published": now.replace(hour=10),
        },
    ]
    
    # Save initial items
    initial_item_objects = [dict_to_item(item) for item in initial_items]
    store.save_many(initial_item_objects)
    
    # Create new items (one new, one existing)
    new_items = [
        {
            "item_id": "item2",  # Existing item - should be overwritten
            "source_type": "rss",
            "source_url": "https://example.com/rss.xml",
            "title": "Updated Article",  # Different title
            "link": "https://example.com/article1",
            "published": now.replace(hour=11),  # Different time
        },
        {
            "item_id": "item3",  # New item
            "source_type": "bilibili",
            "source_url": "https://bilibili.com/video/BV123",
            "title": "Bilibili Video",
            "link": "https://bilibili.com/video/BV123",
            "published": now.replace(hour=12),
        },
    ]
    
    # Save new items
    new_item_objects = [dict_to_item(item) for item in new_items]
    store.save_many(new_item_objects)
    
    # Load all items
    loaded_items = store.load_all()
    
    # Verify we have 3 items total
    assert len(loaded_items) == 3
    
    # Verify item2 was overwritten
    item2 = next(item for item in loaded_items if item.item_id == "item2")
    assert item2.title == "Updated Article"
    assert item2.published == now.replace(hour=11)
    
    # Verify item1 is unchanged
    item1 = next(item for item in loaded_items if item.item_id == "item1")
    assert item1.title == "First Video"
    assert item1.published == now
    
    # Verify item3 was added
    item3 = next(item for item in loaded_items if item.item_id == "item3")
    assert item3.title == "Bilibili Video"
    assert item3.published == now.replace(hour=12)


def test_item_sorting(tmp_path: Path) -> None:
    """Test that items are sorted by published descending, then item_id ascending."""
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Create items with different publish times
    now = datetime.now(timezone.utc)

    items = [
        {
            "item_id": "item1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "First Video",
            "link": "https://www.youtube.com/watch?v=abc123",
            "published": now.replace(hour=10),  # Middle time
        },
        {
            "item_id": "item2",
            "source_type": "rss",
            "source_url": "https://example.com/rss.xml",
            "title": "First Article",
            "link": "https://example.com/article1",
            "published": now.replace(hour=12),  # Latest time
        },
        {
            "item_id": "item3",
            "source_type": "bilibili",
            "source_url": "https://bilibili.com/video/BV123",
            "title": "Bilibili Video",
            "link": "https://bilibili.com/video/BV123",
            "published": now.replace(hour=8),  # Earliest time
        },
    ]
    
    # Save items
    items_objects = [dict_to_item(item) for item in items]

    
    store.save_many(items_objects)
    
    # Load items
    loaded_items = store.load_all()
    
    # Verify sorting (latest first)
    assert len(loaded_items) == 3
    assert loaded_items[0].item_id == "item2"  # Latest (hour=12)
    assert loaded_items[1].item_id == "item1"  # Middle (hour=10)
    assert loaded_items[2].item_id == "item3"  # Earliest (hour=8)


def test_item_sorting_same_published_time(tmp_path: Path) -> None:
    """Test that items with same publish time are sorted by item_id."""
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Create items with same publish time
    now = datetime.now(timezone.utc)

    items = [
        {
            "item_id": "zebra",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Zebra Video",
            "link": "https://www.youtube.com/watch?v=zebra",
            "published": now,  # Same time
        },
        {
            "item_id": "apple",
            "source_type": "rss",
            "source_url": "https://example.com/rss.xml",
            "title": "Apple Article",
            "link": "https://example.com/article1",
            "published": now,  # Same time
        },
        {
            "item_id": "banana",
            "source_type": "bilibili",
            "source_url": "https://bilibili.com/video/BV123",
            "title": "Banana Video",
            "link": "https://bilibili.com/video/BV123",
            "published": now,  # Same time
        },
    ]
    
    # Save items
    items_objects = [dict_to_item(item) for item in items]

    
    store.save_many(items_objects)
    
    # Load items
    loaded_items = store.load_all()
    
    # Verify sorting by item_id (alphabetical)
    assert len(loaded_items) == 3
    assert loaded_items[0].item_id == "apple"   # First alphabetically
    assert loaded_items[1].item_id == "banana"  # Second alphabetically
    assert loaded_items[2].item_id == "zebra"   # Third alphabetically


def test_load_invalid_json(tmp_path: Path) -> None:
    """Test loading from a file with invalid JSON raises ValueError."""
    store_path = tmp_path / "invalid.json"
    store = JsonItemStore(store_path)
    
    # Create file with invalid JSON
    store_path.write_text('{"invalid": json}')
    
    # Loading should raise ValueError
    with pytest.raises(ValueError, match="Invalid JSON"):
        store.load_all()


def test_load_invalid_structure(tmp_path: Path) -> None:
    """Test loading from a file with invalid structure raises ValueError."""
    store_path = tmp_path / "invalid_structure.json"
    store = JsonItemStore(store_path)
    
    # Create file with valid JSON but invalid structure
    store_path.write_text('{"not_items": []}')
    
    # Loading should raise ValueError
    with pytest.raises(ValueError, match="Invalid structure"):
        store.load_all()


def test_load_invalid_items_type(tmp_path: Path) -> None:
    """Test loading from a file where items is not a list raises ValueError."""
    store_path = tmp_path / "invalid_items.json"
    store = JsonItemStore(store_path)
    
    # Create file where items is not a list
    store_path.write_text('{"items": "not a list"}')
    
    # Loading should raise ValueError
    with pytest.raises(ValueError, match="'items' must be a list"):
        store.load_all()


def test_load_invalid_item_type(tmp_path: Path) -> None:
    """Test loading from a file with invalid item type raises ValueError."""
    store_path = tmp_path / "invalid_item.json"
    store = JsonItemStore(store_path)
    
    # Create file where an item is not a dictionary
    store_path.write_text('{"items": [{"valid": "item"}, "not a dict"]}')
    
    # Loading should raise ValueError
    with pytest.raises(ValueError, match="Invalid item in.*item must be a dictionary|Invalid item data"):
        store.load_all()


def test_load_invalid_timestamp(tmp_path: Path) -> None:
    """Test loading from a file with invalid timestamp raises ValueError."""
    store_path = tmp_path / "invalid_timestamp.json"
    store = JsonItemStore(store_path)
    
    # Create file with invalid timestamp
    store_path.write_text('{"items": [{"item_id": "test", "source_type": "youtube", "source_url": "https://example.com", "title": "Test", "link": "https://example.com/test", "published": "not a date"}]}')
    
    # Loading should raise ValueError
    with pytest.raises(ValueError, match="Invalid published timestamp"):
        store.load_all()


def test_save_creates_parent_directory(tmp_path: Path) -> None:
    """Test that save creates parent directory if it doesn't exist."""
    # Use nested path that doesn't exist
    store_path = tmp_path / "nested" / "dir" / "items.json"
    store = JsonItemStore(store_path)
    
    # Verify directory doesn't exist
    assert not store_path.parent.exists()
    
    # Save an item
    now = datetime.now(timezone.utc)

    items = [
        {
            "item_id": "item1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "First Video",
            "link": "https://www.youtube.com/watch?v=abc123",
            "published": now,
        }
    ]
    items_objects = [dict_to_item(item) for item in items]

    
    
    store.save_many(items_objects)
    
    # Verify directory was created and file exists
    assert store_path.parent.exists()
    assert store_path.exists()


def test_datetime_serialization_formats(tmp_path: Path) -> None:
    """Test that datetime serialization handles both Z and +00:00 formats."""
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Create item with datetime
    now = datetime.now(timezone.utc)

    items = [
        {
            "item_id": "item1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "First Video",
            "link": "https://www.youtube.com/watch?v=abc123",
            "published": now,
        }
    ]
    
    # Save items
    items_objects = [dict_to_item(item) for item in items]

    
    store.save_many(items_objects)
    
    # Verify JSON contains Z suffix
    with store_path.open("r") as f:
        data = json.load(f)
    
    assert data["items"][0]["published"].endswith("Z")
    
    # Load items
    loaded_items = store.load_all()
    
    # Verify datetime is correctly parsed
    assert loaded_items[0].published == now
    assert loaded_items[0].published.tzinfo == timezone.utc


def test_save_items_without_item_id(tmp_path: Path) -> None:
    """Test saving items - all items must have item_id in new implementation."""
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Create items with item_id (all items must have item_id now)
    now = datetime.now(timezone.utc)
    items = [
        {
            "item_id": "item1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "First Video",
            "link": "https://www.youtube.com/watch?v=item1",
            "published": now,
        },
        {
            "item_id": "item2",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Second Video",
            "link": "https://www.youtube.com/watch?v=item2",
            "published": now,
        },
    ]
    
    # Save items
    items_objects = [dict_to_item(item) for item in items]
    store.save_many(items_objects)
    
    # Load items
    loaded_items = store.load_all()
    
    # Verify all items were saved
    assert len(loaded_items) == 2
    assert loaded_items[0].item_id == "item1"
    assert loaded_items[1].item_id == "item2"
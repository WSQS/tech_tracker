"""Tests for item diff utilities."""

from datetime import datetime, timezone

import pytest

from tech_tracker.item_diff import diff_new_items


def test_diff_new_items_old_empty_returns_all_new() -> None:
    """Test that when old_items is empty, all new_items are returned."""
    old_items = []
    
    new_items = [
        {
            "item_id": "item1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "First Video",
            "link": "https://www.youtube.com/watch?v=abc123",
            "published": datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
        },
        {
            "item_id": "item2",
            "source_type": "rss",
            "source_url": "https://example.com/rss.xml",
            "title": "First Article",
            "link": "https://example.com/article1",
            "published": datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        },
    ]
    
    result = diff_new_items(old_items, new_items)
    
    # Should return all items in the same order
    assert len(result) == 2
    assert result[0]["item_id"] == "item1"
    assert result[1]["item_id"] == "item2"


def test_diff_new_items_new_empty_returns_empty() -> None:
    """Test that when new_items is empty, empty list is returned."""
    old_items = [
        {
            "item_id": "existing1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Existing Video",
            "link": "https://www.youtube.com/watch?v=existing1",
            "published": datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
        }
    ]
    
    new_items = []
    
    result = diff_new_items(old_items, new_items)
    
    assert result == []


def test_diff_new_items_partial_overlap_returns_only_new() -> None:
    """Test that only items with new IDs are returned."""
    old_items = [
        {
            "item_id": "existing1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Existing Video",
            "link": "https://www.youtube.com/watch?v=existing1",
            "published": datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
        },
        {
            "item_id": "existing2",
            "source_type": "rss",
            "source_url": "https://example.com/rss.xml",
            "title": "Existing Article",
            "link": "https://example.com/article1",
            "published": datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        },
    ]
    
    new_items = [
        {
            "item_id": "existing1",  # Existing ID
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Updated Video",  # Different title but same ID
            "link": "https://www.youtube.com/watch?v=existing1",
            "published": datetime(2023, 12, 20, 11, 0, 0, tzinfo=timezone.utc),
        },
        {
            "item_id": "new1",  # New ID
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC456",
            "title": "New Video",
            "link": "https://www.youtube.com/watch?v=new1",
            "published": datetime(2023, 12, 20, 12, 0, 0, tzinfo=timezone.utc),
        },
        {
            "item_id": "new2",  # New ID
            "source_type": "bilibili",
            "source_url": "https://bilibili.com/video/BV123",
            "title": "New Bilibili Video",
            "link": "https://bilibili.com/video/BV123",
            "published": datetime(2023, 12, 20, 13, 0, 0, tzinfo=timezone.utc),
        },
    ]
    
    result = diff_new_items(old_items, new_items)
    
    # Should only return items with new IDs
    assert len(result) == 2
    assert result[0]["item_id"] == "new1"
    assert result[1]["item_id"] == "new2"
    
    # Verify the order is preserved from new_items
    assert result[0]["title"] == "New Video"
    assert result[1]["title"] == "New Bilibili Video"


def test_diff_new_items_no_ids_in_old_or_new() -> None:
    """Test behavior when items have no item_id."""
    old_items = [
        {
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Video without ID",
            "link": "https://www.youtube.com/watch?v=abc123",
            "published": datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
        }
    ]
    
    new_items = [
        {
            "source_type": "rss",
            "source_url": "https://example.com/rss.xml",
            "title": "Article without ID",
            "link": "https://example.com/article1",
            "published": datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        }
    ]
    
    result = diff_new_items(old_items, new_items)
    
    # Should return empty list since no items have item_id
    assert result == []


def test_diff_new_items_duplicate_ids_in_old_items() -> None:
    """Test behavior when old_items has duplicate item_ids."""
    old_items = [
        {
            "item_id": "duplicate1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "First Instance",
            "link": "https://www.youtube.com/watch?v=duplicate1",
            "published": datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
        },
        {
            "item_id": "duplicate1",  # Duplicate ID
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC456",
            "title": "Second Instance",
            "link": "https://www.youtube.com/watch?v=duplicate1",
            "published": datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        },
    ]
    
    new_items = [
        {
            "item_id": "duplicate1",  # ID exists in old_items
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC789",
            "title": "Third Instance",
            "link": "https://www.youtube.com/watch?v=duplicate1",
            "published": datetime(2023, 12, 20, 11, 0, 0, tzinfo=timezone.utc),
        },
        {
            "item_id": "unique1",  # Unique ID
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC789",
            "title": "Unique Video",
            "link": "https://www.youtube.com/watch?v=unique1",
            "published": datetime(2023, 12, 20, 12, 0, 0, tzinfo=timezone.utc),
        },
    ]
    
    result = diff_new_items(old_items, new_items)
    
    # Should only return the unique item
    assert len(result) == 1
    assert result[0]["item_id"] == "unique1"


def test_diff_new_items_duplicate_ids_in_new_items() -> None:
    """Test behavior when new_items has duplicate item_ids."""
    old_items = [
        {
            "item_id": "existing1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Existing Video",
            "link": "https://www.youtube.com/watch?v=existing1",
            "published": datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
        }
    ]
    
    new_items = [
        {
            "item_id": "existing1",  # ID exists in old_items
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC456",
            "title": "Updated Existing",
            "link": "https://www.youtube.com/watch?v=existing1",
            "published": datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        },
        {
            "item_id": "duplicate1",  # Same ID as below
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC789",
            "title": "First Duplicate",
            "link": "https://www.youtube.com/watch?v=duplicate1",
            "published": datetime(2023, 12, 20, 11, 0, 0, tzinfo=timezone.utc),
        },
        {
            "item_id": "duplicate1",  # Same ID as above
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC789",
            "title": "Second Duplicate",
            "link": "https://www.youtube.com/watch?v=duplicate1",
            "published": datetime(2023, 12, 20, 12, 0, 0, tzinfo=timezone.utc),
        },
    ]
    
    result = diff_new_items(old_items, new_items)
    
    # Should return both items with duplicate IDs since 'duplicate1' doesn't exist in old_items
    assert len(result) == 2
    assert result[0]["item_id"] == "duplicate1"
    assert result[1]["item_id"] == "duplicate1"
    assert result[0]["title"] == "First Duplicate"
    assert result[1]["title"] == "Second Duplicate"
    
    # Verify order is preserved from new_items
    assert result[0]["source_url"] == "https://www.youtube.com/channel/UC789"
    assert result[1]["source_url"] == "https://www.youtube.com/channel/UC789"


def test_diff_new_items_preserve_order() -> None:
    """Test that the order of new items is preserved."""
    old_items = [
        {
            "item_id": "existing1",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/channel/UC123",
            "title": "Existing Video",
            "link": "link1",
            "published": datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc),
        }
    ]
    
    # Create new items in a specific order
    new_items = []
    for i in range(3):
        new_items.append({
            "item_id": f"new{i}",
            "source_type": "youtube",
            "source_url": f"https://www.youtube.com/channel/UC{i}",
            "title": f"Video {i}",
            "link": f"link{i}",
            "published": datetime(2023, 12, 20, 10 + i, 0, 0, tzinfo=timezone.utc),
        })
    
    result = diff_new_items(old_items, new_items)
    
    # Verify all three new items are returned in the same order
    assert len(result) == 3
    assert result[0]["item_id"] == "new0"
    assert result[0]["title"] == "Video 0"
    assert result[1]["item_id"] == "new1"
    assert result[1]["title"] == "Video 1"
    assert result[2]["item_id"] == "new2"
    assert result[2]["title"] == "Video 2"
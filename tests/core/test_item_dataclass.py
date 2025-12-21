from datetime import datetime, timezone
from tech_tracker import Item


def test_item_from_dict_to_dict_round_trip():
    """Test Item.from_dict and Item.to_dict round-trip conversion."""
    # Sample data from the specification
    sample_dict = {
        "item_id": "L7x2ufU1c9Y",
        "source_type": "youtube",
        "source_url": "https://www.youtube.com/channel/UCEbYhDd6c6vngsF5PQpFVWg",
        "title": "My thoughts on Y Combinator",
        "link": "https://www.youtube.com/watch?v=L7x2ufU1c9Y",
        "published": "2025-12-20T04:39:33Z",
        "seen": False,
    }
    
    # Create Item from dict
    item = Item.from_dict(sample_dict)
    
    # Verify Item properties
    assert item.item_id == "L7x2ufU1c9Y"
    assert item.source_type == "youtube"
    assert item.source_url == "https://www.youtube.com/channel/UCEbYhDd6c6vngsF5PQpFVWg"
    assert item.title == "My thoughts on Y Combinator"
    assert item.link == "https://www.youtube.com/watch?v=L7x2ufU1c9Y"
    assert item.published == datetime(2025, 12, 20, 4, 39, 33, tzinfo=timezone.utc)
    assert item.seen is False
    
    # Convert back to dict
    result_dict = item.to_dict()
    
    # Verify round-trip produces same dict
    assert result_dict == sample_dict


def test_item_from_dict_with_datetime():
    """Test Item.from_dict with datetime input."""
    dt = datetime(2025, 12, 20, 4, 39, 33, tzinfo=timezone.utc)
    sample_dict = {
        "item_id": "L7x2ufU1c9Y",
        "source_type": "youtube",
        "source_url": "https://www.youtube.com/channel/UCEbYhDd6c6vngsF5PQpFVWg",
        "title": "My thoughts on Y Combinator",
        "link": "https://www.youtube.com/watch?v=L7x2ufU1c9Y",
        "published": dt,
        "seen": True,
    }
    
    item = Item.from_dict(sample_dict)
    assert item.published == dt
    assert item.seen is True


def test_item_from_dict_without_seen_field():
    """Test Item.from_dict without seen field for backward compatibility."""
    sample_dict = {
        "item_id": "L7x2ufU1c9Y",
        "source_type": "youtube",
        "source_url": "https://www.youtube.com/channel/UCEbYhDd6c6vngsF5PQpFVWg",
        "title": "My thoughts on Y Combinator",
        "link": "https://www.youtube.com/watch?v=L7x2ufU1c9Y",
        "published": "2025-12-20T04:39:33Z",
    }
    
    # Create Item from dict without seen field
    item = Item.from_dict(sample_dict)
    
    # Verify default seen value
    assert item.seen is False
    
    # Convert back to dict should include seen field
    result_dict = item.to_dict()
    assert "seen" in result_dict
    assert result_dict["seen"] is False


def test_item_seen_field_round_trip():
    """Test seen field round-trip with both True and False values."""
    base_dict = {
        "item_id": "test123",
        "source_type": "youtube",
        "source_url": "https://www.youtube.com/channel/UC123",
        "title": "Test Video",
        "link": "https://www.youtube.com/watch?v=test123",
        "published": "2023-12-20T09:00:00Z",
    }
    
    # Test seen=True
    seen_true_dict = {**base_dict, "seen": True}
    item_seen_true = Item.from_dict(seen_true_dict)
    assert item_seen_true.seen is True
    result_true_dict = item_seen_true.to_dict()
    assert result_true_dict["seen"] is True
    
    # Test seen=False
    seen_false_dict = {**base_dict, "seen": False}
    item_seen_false = Item.from_dict(seen_false_dict)
    assert item_seen_false.seen is False
    result_false_dict = item_seen_false.to_dict()
    assert result_false_dict["seen"] is False


def test_item_from_dict_invalid_seen_field():
    """Test Item.from_dict with invalid seen field type."""
    base_dict = {
        "item_id": "test123",
        "source_type": "youtube",
        "source_url": "https://www.youtube.com/channel/UC123",
        "title": "Test Video",
        "link": "https://www.youtube.com/watch?v=test123",
        "published": "2023-12-20T09:00:00Z",
    }
    
    # Test with string instead of bool
    invalid_seen_dict = {**base_dict, "seen": "true"}
    try:
        Item.from_dict(invalid_seen_dict)
        assert False, "Expected ValueError for invalid seen field type"
    except ValueError as e:
        assert "Seen field must be boolean" in str(e)
    
    # Test with int instead of bool
    invalid_seen_dict = {**base_dict, "seen": 1}
    try:
        Item.from_dict(invalid_seen_dict)
        assert False, "Expected ValueError for invalid seen field type"
    except ValueError as e:
        assert "Seen field must be boolean" in str(e)
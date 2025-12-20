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
    }
    
    item = Item.from_dict(sample_dict)
    assert item.published == dt
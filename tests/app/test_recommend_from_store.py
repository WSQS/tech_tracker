"""Tests for recommend_from_store function."""

from datetime import datetime, timezone
from pathlib import Path

from tech_tracker.app.recommend import LatestRecommender, recommend_from_store
from tech_tracker.item import Item
from tech_tracker.item_store import JsonItemStore


def test_recommend_from_store_returns_recommend_result(tmp_path: Path) -> None:
    """Test a) recommend_from_store returns RecommendResult."""
    # Create store
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Create recommender
    recommender = LatestRecommender()
    
    # Get recommendation
    result = recommend_from_store(store, recommender)
    
    # Verify result type
    assert hasattr(result, 'items')
    assert hasattr(result, 'meta')
    assert isinstance(result.items, list)
    assert isinstance(result.meta, dict)


def test_recommend_from_store_with_latest_recommender_sorting_and_limit(tmp_path: Path) -> None:
    """Test b) using LatestRecommender, result items order follows published desc + item_id asc, and limit truncation."""
    # Create store
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Create test items with different published times and IDs
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="zebra",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="Zebra Item",
            link="https://youtube.com/watch?v=zebra",
            published=base_time,  # Earliest time
        ),
        Item(
            item_id="apple",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="Apple Item",
            link="https://youtube.com/watch?v=apple",
            published=base_time.replace(hour=12),  # Latest time
        ),
        Item(
            item_id="banana",
            source_type="youtube",
            source_url="https://youtube.com/channel/3",
            title="Banana Item",
            link="https://youtube.com/watch?v=banana",
            published=base_time.replace(hour=12),  # Same latest time as apple
        ),
        Item(
            item_id="cherry",
            source_type="youtube",
            source_url="https://youtube.com/channel/4",
            title="Cherry Item",
            link="https://youtube.com/watch?v=cherry",
            published=base_time.replace(hour=11),  # Middle time
        ),
    ]
    
    # Save items to store
    store.save_many(items)
    
    # Create recommender
    recommender = LatestRecommender()
    
    # Test with limit less than total items
    result = recommend_from_store(store, recommender, limit=3)
    
    # Verify sorting order and limit truncation
    assert len(result.items) == 3
    
    # Should be sorted by published desc, then item_id asc
    # Expected order: apple (hour=12), banana (hour=12), cherry (hour=11)
    expected_order = ["apple", "banana", "cherry"]
    actual_order = [item.item_id for item in result.items]
    assert actual_order == expected_order


def test_recommend_from_store_meta_contains_source_and_recommender(tmp_path: Path) -> None:
    """Test c) result.meta contains source/store and recommender name (plus LatestRecommender's original meta)."""
    # Create store
    store_path = tmp_path / "items.json"
    store = JsonItemStore(store_path)
    
    # Create test items
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="item1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="Item 1",
            link="https://youtube.com/watch?v=item1",
            published=base_time,
        ),
        Item(
            item_id="item2",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="Item 2",
            link="https://youtube.com/watch?v=item2",
            published=base_time.replace(hour=11),
        ),
    ]
    
    # Save items to store
    store.save_many(items)
    
    # Create recommender
    recommender = LatestRecommender()
    
    # Test with custom limit and context
    result = recommend_from_store(store, recommender, limit=1, context={"test": "value"})
    
    # Verify meta contains required information
    assert "source" in result.meta
    assert result.meta["source"] == "store"
    
    assert "recommender" in result.meta
    assert result.meta["recommender"] == "latest"
    
    # Verify LatestRecommender's original meta is preserved
    assert "strategy" in result.meta
    assert result.meta["strategy"] == "latest"
    
    assert "limit" in result.meta
    assert result.meta["limit"] == 1
    
    # Verify items are limited correctly
    assert len(result.items) == 1
    assert result.items[0].item_id == "item2"  # Latest item
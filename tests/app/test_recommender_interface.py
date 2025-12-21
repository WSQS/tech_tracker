"""Tests for recommender interface and LatestRecommender implementation."""

from datetime import datetime, timezone

from tech_tracker.app.recommend import LatestRecommender, RecommendRequest, RecommendResult
from tech_tracker.item import Item


def test_latest_recommender_name() -> None:
    """Test a) LatestRecommender.name == "latest"."""
    recommender = LatestRecommender()
    assert recommender.name == "latest"


def test_latest_recommender_returns_recommend_result() -> None:
    """Test b) recommend returns RecommendResult, and result.items is list[Item]."""
    recommender = LatestRecommender()
    
    # Create test items
    now = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="item1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="Item 1",
            link="https://youtube.com/watch?v=1",
            published=now,
        ),
        Item(
            item_id="item2",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="Item 2",
            link="https://youtube.com/watch?v=2",
            published=now,
        ),
    ]
    
    # Create request
    req = RecommendRequest(items=items, limit=10)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify result type and structure
    assert isinstance(result, RecommendResult)
    assert isinstance(result.items, list)
    assert all(isinstance(item, Item) for item in result.items)
    assert isinstance(result.meta, dict)


def test_latest_recommender_sorting_order() -> None:
    """Test c) sorting rules are correct (published desc + item_id asc)."""
    recommender = LatestRecommender()
    
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
    
    # Create request with high limit to get all items
    req = RecommendRequest(items=items, limit=10)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify sorting order
    assert len(result.items) == 4
    
    # Should be sorted by published desc, then item_id asc
    # Expected order: apple (hour=12), banana (hour=12), cherry (hour=11), zebra (hour=10)
    expected_order = ["apple", "banana", "cherry", "zebra"]
    actual_order = [item.item_id for item in result.items]
    assert actual_order == expected_order


def test_latest_recommender_limit_truncation() -> None:
    """Test d) limit truncation is correct."""
    recommender = LatestRecommender()
    
    # Create test items
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id=f"item{i}",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title=f"Item {i}",
            link=f"https://youtube.com/watch?v={i}",
            published=base_time.replace(hour=10+i),
        )
        for i in range(5)  # Create 5 items
    ]
    
    # Test with limit less than total items
    req = RecommendRequest(items=items, limit=3)
    result = recommender.recommend(req)
    
    # Verify only 3 items are returned
    assert len(result.items) == 3
    
    # Verify meta contains the limit
    assert result.meta["limit"] == 3
    assert result.meta["strategy"] == "latest"
    
    # Verify the items are the latest ones (highest published times)
    expected_ids = ["item4", "item3", "item2"]  # Latest 3 items
    actual_ids = [item.item_id for item in result.items]
    assert actual_ids == expected_ids
    
    # Test with limit greater than total items
    req = RecommendRequest(items=items, limit=10)
    result = recommender.recommend(req)
    
    # Should return all items
    assert len(result.items) == 5
    assert result.meta["limit"] == 10
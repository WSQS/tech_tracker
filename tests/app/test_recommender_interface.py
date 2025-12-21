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


def test_latest_recommender_filters_seen_items() -> None:
    """Test that LatestRecommender filters out seen items when unseen items are available."""
    recommender = LatestRecommender()
    
    # Create test items with mixed seen status
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="seen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="Seen Item 1",
            link="https://youtube.com/watch?v=seen1",
            published=base_time.replace(hour=12),  # Latest time, but seen
            seen=True,
        ),
        Item(
            item_id="unseen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="Unseen Item 1",
            link="https://youtube.com/watch?v=unseen1",
            published=base_time.replace(hour=11),  # Earlier time, but unseen
            seen=False,
        ),
        Item(
            item_id="seen2",
            source_type="youtube",
            source_url="https://youtube.com/channel/3",
            title="Seen Item 2",
            link="https://youtube.com/watch?v=seen2",
            published=base_time.replace(hour=10),  # Earliest time, and seen
            seen=True,
        ),
    ]
    
    # Create request
    req = RecommendRequest(items=items, limit=10)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify only unseen items are returned
    assert len(result.items) == 1
    assert result.items[0].item_id == "unseen1"
    assert result.items[0].seen is False
    
    # Verify metadata indicates filtering was applied
    assert result.meta["filtered"] is True
    assert result.meta["total_items"] == 3
    assert result.meta["unseen_items"] == 1


def test_latest_recommender_fallback_when_all_seen() -> None:
    """Test that LatestRecommender falls back to all items when all items are seen."""
    recommender = LatestRecommender()
    
    # Create test items with all seen status
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="seen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="Seen Item 1",
            link="https://youtube.com/watch?v=seen1",
            published=base_time.replace(hour=12),  # Latest time
            seen=True,
        ),
        Item(
            item_id="seen2",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="Seen Item 2",
            link="https://youtube.com/watch?v=seen2",
            published=base_time.replace(hour=11),  # Middle time
            seen=True,
        ),
        Item(
            item_id="seen3",
            source_type="youtube",
            source_url="https://youtube.com/channel/3",
            title="Seen Item 3",
            link="https://youtube.com/watch?v=seen3",
            published=base_time.replace(hour=10),  # Earliest time
            seen=True,
        ),
    ]
    
    # Create request
    req = RecommendRequest(items=items, limit=10)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify all items are returned (fallback behavior)
    assert len(result.items) == 3
    
    # Verify items are sorted correctly (published desc, then item_id asc)
    expected_order = ["seen1", "seen2", "seen3"]
    actual_order = [item.item_id for item in result.items]
    assert actual_order == expected_order
    
    # Verify all returned items are seen (since all items are seen)
    assert all(item.seen is True for item in result.items)
    
    # Verify metadata indicates no filtering was applied (fallback)
    assert result.meta["filtered"] is False
    assert result.meta["total_items"] == 3
    assert result.meta["unseen_items"] == 0


def test_latest_recommender_mixed_seen_with_limit() -> None:
    """Test LatestRecommender with mixed seen items and limit applied."""
    recommender = LatestRecommender()
    
    # Create test items with mixed seen status
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="seen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="Seen Item 1",
            link="https://youtube.com/watch?v=seen1",
            published=base_time.replace(hour=12),
            seen=True,
        ),
        Item(
            item_id="unseen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="Unseen Item 1",
            link="https://youtube.com/watch?v=unseen1",
            published=base_time.replace(hour=11),
            seen=False,
        ),
        Item(
            item_id="unseen2",
            source_type="youtube",
            source_url="https://youtube.com/channel/3",
            title="Unseen Item 2",
            link="https://youtube.com/watch?v=unseen2",
            published=base_time.replace(hour=10),
            seen=False,
        ),
    ]
    
    # Create request with limit
    req = RecommendRequest(items=items, limit=1)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify only the latest unseen item is returned
    assert len(result.items) == 1
    assert result.items[0].item_id == "unseen1"
    assert result.items[0].seen is False
    
    # Verify metadata
    assert result.meta["filtered"] is True
    assert result.meta["total_items"] == 3
    assert result.meta["unseen_items"] == 2
    assert result.meta["limit"] == 1
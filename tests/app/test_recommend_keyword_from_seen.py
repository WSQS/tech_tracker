"""Tests for recommend_keyword_from_seen pure function."""

from datetime import datetime, timezone

from tech_tracker.app.recommend import recommend_keyword_from_seen
from tech_tracker.item import Item


def test_recommend_keyword_from_seen_basic():
    """Test basic keyword extraction and recommendation."""
    # Create test items
    seen_item1 = Item(
        item_id="youtube:abc123",
        source_type="youtube",
        source_url="https://youtube.com/channel/test1",
        title="Python Programming Tutorial",
        link="https://youtube.com/watch?v=abc123",
        published=datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        seen=True
    )
    
    unseen_item1 = Item(
        item_id="youtube:def456",
        source_type="youtube",
        source_url="https://youtube.com/channel/test2",
        title="Advanced Python Guide",
        link="https://youtube.com/watch?v=def456",
        published=datetime(2023, 12, 21, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    
    unseen_item2 = Item(
        item_id="youtube:ghi789",
        source_type="youtube",
        source_url="https://youtube.com/channel/test3",
        title="JavaScript Basics",
        link="https://youtube.com/watch?v=ghi789",
        published=datetime(2023, 12, 22, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    
    items = [seen_item1, unseen_item1, unseen_item2]
    
    # Test recommendation
    result = recommend_keyword_from_seen(items)
    
    # Should recommend unseen_item1 (contains "python") first
    assert len(result) == 2
    assert result[0].item_id == "youtube:def456"  # Python Guide
    assert result[1].item_id == "youtube:ghi789"  # JavaScript (no matching keywords, score=0)


def test_keyword_weights_frequency():
    """Test that keyword weights are based on frequency in seen items."""
    # Create seen items with "python" appearing multiple times
    seen_item1 = Item(
        item_id="youtube:abc123",
        source_type="youtube",
        source_url="https://youtube.com/channel/test1",
        title="Python Programming",
        link="https://youtube.com/watch?v=abc123",
        published=datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        seen=True
    )
    
    seen_item2 = Item(
        item_id="youtube:def456",
        source_type="youtube",
        source_url="https://youtube.com/channel/test2",
        title="Python Tutorial",
        link="https://youtube.com/watch?v=def456",
        published=datetime(2023, 12, 21, 10, 0, 0, tzinfo=timezone.utc),
        seen=True
    )
    
    seen_item3 = Item(
        item_id="youtube:ghi789",
        source_type="youtube",
        source_url="https://youtube.com/channel/test3",
        title="JavaScript Guide",
        link="https://youtube.com/watch?v=ghi789",
        published=datetime(2023, 12, 22, 10, 0, 0, tzinfo=timezone.utc),
        seen=True
    )
    
    # Unseen items
    unseen_python = Item(
        item_id="python:new123",
        source_type="youtube",
        source_url="https://youtube.com/channel/python",
        title="Python Programming Tutorial",
        link="https://youtube.com/watch?v=new123",
        published=datetime(2023, 12, 23, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    
    unseen_javascript = Item(
        item_id="javascript:new456",
        source_type="youtube",
        source_url="https://youtube.com/channel/javascript",
        title="JavaScript Guide",
        link="https://youtube.com/watch?v=new456",
        published=datetime(2023, 12, 23, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    
    items = [seen_item1, seen_item2, seen_item3, unseen_python, unseen_javascript]
    
    result = recommend_keyword_from_seen(items)
    
    # Python should rank first (weight=2) vs JavaScript (weight=1)
    assert len(result) == 2
    assert result[0].item_id == "python:new123"  # Python with higher weight
    assert result[1].item_id == "javascript:new456"  # JavaScript with lower weight


def test_unseen_priority_with_fallback():
    """Test that unseen items are prioritized with fallback to all items."""
    # Create seen items
    seen_item1 = Item(
        item_id="youtube:seen1",
        source_type="youtube",
        source_url="https://youtube.com/channel/test1",
        title="Python Programming",
        link="https://youtube.com/watch?v=seen1",
        published=datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        seen=True
    )
    
    seen_item2 = Item(
        item_id="youtube:seen2",
        source_type="youtube",
        source_url="https://youtube.com/channel/test2",
        title="Python Tutorial",
        link="https://youtube.com/watch?v=seen2",
        published=datetime(2023, 12, 21, 10, 0, 0, tzinfo=timezone.utc),
        seen=True
    )
    
    # Case 1: Has unseen items
    unseen_item = Item(
        item_id="youtube:unseen1",
        source_type="youtube",
        source_url="https://youtube.com/channel/test3",
        title="Python Guide",
        link="https://youtube.com/watch?v=unseen1",
        published=datetime(2023, 12, 22, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    
    items_with_unseen = [seen_item1, seen_item2, unseen_item]
    result_with_unseen = recommend_keyword_from_seen(items_with_unseen)
    
    # Should only return unseen items
    assert len(result_with_unseen) == 1
    assert result_with_unseen[0].item_id == "youtube:unseen1"
    
    # Case 2: No unseen items (fallback to all items)
    items_all_seen = [seen_item1, seen_item2]
    result_all_seen = recommend_keyword_from_seen(items_all_seen)
    
    # Should return seen items as candidates
    assert len(result_all_seen) == 2
    assert all(item.seen for item in result_all_seen)


def test_sorting_stability():
    """Test sorting stability: score desc, published desc, item_id asc."""
    # Create seen items for keyword weights
    seen_item1 = Item(
        item_id="youtube:seen1",
        source_type="youtube",
        source_url="https://youtube.com/channel/test1",
        title="Python Programming Tutorial",
        link="https://youtube.com/watch?v=seen1",
        published=datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        seen=True
    )
    
    # Create unseen items with different scores and times
    unseen_item1 = Item(
        item_id="youtube:bbb",  # Later in alphabet
        source_type="youtube",
        source_url="https://youtube.com/channel/test2",
        title="Python Programming",  # Score: 2 (python + programming)
        link="https://youtube.com/watch?v=bbb",
        published=datetime(2023, 12, 21, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    
    unseen_item2 = Item(
        item_id="youtube:aaa",  # Earlier in alphabet
        source_type="youtube",
        source_url="https://youtube.com/channel/test3",
        title="Python Programming",  # Score: 2 (python + programming)
        link="https://youtube.com/watch?v=aaa",
        published=datetime(2023, 12, 21, 10, 0, 0, tzinfo=timezone.utc),  # Same time
        seen=False
    )
    
    unseen_item3 = Item(
        item_id="youtube:ccc",
        source_type="youtube",
        source_url="https://youtube.com/channel/test4",
        title="Tutorial Guide",  # Score: 1 (tutorial)
        link="https://youtube.com/watch?v=ccc",
        published=datetime(2023, 12, 22, 10, 0, 0, tzinfo=timezone.utc),  # Later time
        seen=False
    )
    
    items = [seen_item1, unseen_item1, unseen_item2, unseen_item3]
    result = recommend_keyword_from_seen(items)
    
    # Expected order:
    # 1. unseen_item2/1 (score=2) - sorted by item_id asc (aaa before bbb)
    # 2. unseen_item3 (score=1)
    assert len(result) == 3
    assert result[0].item_id == "youtube:aaa"  # Same score, same time, earlier ID
    assert result[1].item_id == "youtube:bbb"  # Same score, same time, later ID
    assert result[2].item_id == "youtube:ccc"  # Lower score


def test_limit_truncation():
    """Test that limit parameter properly truncates results."""
    # Create seen items
    seen_item = Item(
        item_id="youtube:seen1",
        source_type="youtube",
        source_url="https://youtube.com/channel/test1",
        title="Python Programming",
        link="https://youtube.com/watch?v=seen1",
        published=datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        seen=True
    )
    
    # Create many unseen items
    unseen_items = []
    for i in range(5):
        unseen_items.append(Item(
            item_id=f"youtube:unseen{i}",
            source_type="youtube",
            source_url=f"https://youtube.com/channel/test{i+2}",
            title=f"Python Tutorial {i}",
            link=f"https://youtube.com/watch?v=unseen{i}",
            published=datetime(2023, 12, 21 + i, 10, 0, 0, tzinfo=timezone.utc),
            seen=False
        ))
    
    items = [seen_item] + unseen_items
    
    # Test with limit=3
    result = recommend_keyword_from_seen(items, limit=3)
    assert len(result) == 3
    
    # Test with limit=10 (more than available)
    result = recommend_keyword_from_seen(items, limit=10)
    assert len(result) == 5  # All unseen items


def test_tokenization_case_and_separators():
    """Test tokenization with different cases and separators."""
    # Create seen item with mixed case and separators
    seen_item = Item(
        item_id="youtube:seen1",
        source_type="youtube",
        source_url="https://youtube.com/channel/test1",
        title="Python-Programming_Tutorial, Guide",
        link="https://youtube.com/watch?v=seen1",
        published=datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        seen=True
    )
    
    # Create unseen item with different case
    unseen_item = Item(
        item_id="youtube:unseen1",
        source_type="youtube",
        source_url="https://youtube.com/channel/test2",
        title="PYTHON programming guide",
        link="https://youtube.com/watch?v=unseen1",
        published=datetime(2023, 12, 21, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    
    items = [seen_item, unseen_item]
    result = recommend_keyword_from_seen(items)
    
    # Should match regardless of case (python, programming, tutorial, guide)
    assert len(result) == 1
    assert result[0].item_id == "youtube:unseen1"


def test_no_seen_items():
    """Test behavior when no items are seen."""
    # Create only unseen items
    unseen_item1 = Item(
        item_id="youtube:unseen1",
        source_type="youtube",
        source_url="https://youtube.com/channel/test1",
        title="Python Programming",
        link="https://youtube.com/watch?v=unseen1",
        published=datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    
    unseen_item2 = Item(
        item_id="youtube:unseen2",
        source_type="youtube",
        source_url="https://youtube.com/channel/test2",
        title="JavaScript Tutorial",
        link="https://youtube.com/watch?v=unseen2",
        published=datetime(2023, 12, 21, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    
    items = [unseen_item1, unseen_item2]
    result = recommend_keyword_from_seen(items)
    
    # Should return empty list when no seen items
    assert len(result) == 0


def test_empty_items_list():
    """Test behavior with empty items list."""
    result = recommend_keyword_from_seen([])
    assert len(result) == 0


def test_recommend_keyword_from_seen_deduplicate_tokens():
    """Test that duplicate tokens within a title are only counted once."""
    # Create seen items with specific keyword weights
    seen_item1 = Item(
        item_id="seen:python1",
        source_type="youtube",
        source_url="https://youtube.com/channel/python",
        title="Python Programming Tutorial",
        link="https://youtube.com/watch?v=python1",
        published=datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
        seen=True
    )
    seen_item2 = Item(
        item_id="seen:async1",
        source_type="youtube",
        source_url="https://youtube.com/channel/async",
        title="Async Programming Guide",
        link="https://youtube.com/watch?v=async1",
        published=datetime(2023, 12, 21, 10, 0, 0, tzinfo=timezone.utc),
        seen=True
    )
    
    # Create unseen items with duplicate tokens
    # "python python async" - python appears twice, should only count once
    unseen_item1 = Item(
        item_id="unseen:duplicate_python",
        source_type="youtube",
        source_url="https://youtube.com/channel/duplicate",
        title="python python async",  # python appears twice
        link="https://youtube.com/watch?v=duplicate",
        published=datetime(2023, 12, 22, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    # "async async python" - async appears twice, should only count once
    unseen_item2 = Item(
        item_id="unseen:duplicate_async",
        source_type="youtube",
        source_url="https://youtube.com/channel/duplicate2",
        title="async async python",  # async appears twice
        link="https://youtube.com/watch?v=duplicate2",
        published=datetime(2023, 12, 23, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    # "python async" - no duplicates
    unseen_item3 = Item(
        item_id="unseen:no_duplicates",
        source_type="youtube",
        source_url="https://youtube.com/channel/normal",
        title="python async",  # no duplicates
        link="https://youtube.com/watch?v=normal",
        published=datetime(2023, 12, 24, 10, 0, 0, tzinfo=timezone.utc),
        seen=False
    )
    
    items = [seen_item1, seen_item2, unseen_item1, unseen_item2, unseen_item3]
    
    # Get recommendations
    result = recommend_keyword_from_seen(items, limit=10)
    
    # Expected keyword weights from seen items:
    # "python": 1 (from "Python Programming Tutorial")
    # "programming": 1 (from "Python Programming Tutorial") 
    # "tutorial": 1 (from "Python Programming Tutorial")
    # "async": 1 (from "Async Programming Guide")
    # "guide": 1 (from "Async Programming Guide")
    
    # Expected scores (with deduplication):
    # unseen_item1 ("python python async"): python(1) + async(1) = 2
    # unseen_item2 ("async async python"): async(1) + python(1) = 2  
    # unseen_item3 ("python async"): python(1) + async(1) = 2
    
    # All three items should have the same score (2), so sorting should be by published desc
    assert len(result) == 3
    
    # Check ordering by published time (newest first)
    assert result[0].item_id == "unseen:no_duplicates"  # 2023-12-24 (newest)
    assert result[1].item_id == "unseen:duplicate_async"  # 2023-12-23  
    assert result[2].item_id == "unseen:duplicate_python"  # 2023-12-22 (oldest)
    
    # Verify that all items have the same score (2) by checking their relative ordering
    # Since scores are equal, they should be sorted by published time descending
    assert result[0].published > result[1].published > result[2].published
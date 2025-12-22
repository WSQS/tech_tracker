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


def test_keyword_from_seen_recommender_name() -> None:
    """Test a) KeywordFromSeenRecommender.name == "keyword_from_seen"."""
    from tech_tracker.app.recommend import KeywordFromSeenRecommender
    
    recommender = KeywordFromSeenRecommender()
    assert recommender.name == "keyword_from_seen"


def test_keyword_from_seen_recommender_returns_recommend_result() -> None:
    """Test b) recommend returns RecommendResult, and result.items is list[Item]."""
    from tech_tracker.app.recommend import KeywordFromSeenRecommender
    
    recommender = KeywordFromSeenRecommender()
    
    # Create test items
    now = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="youtube:seen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="Python Programming Tutorial",
            link="https://youtube.com/watch?v=seen1",
            published=now,
            seen=True
        ),
        Item(
            item_id="youtube:unseen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="Advanced Python Guide",
            link="https://youtube.com/watch?v=unseen1",
            published=datetime(2023, 12, 21, 15, 0, 0, tzinfo=timezone.utc),
            seen=False
        ),
        Item(
            item_id="youtube:unseen2",
            source_type="youtube",
            source_url="https://youtube.com/channel/3",
            title="JavaScript Basics",
            link="https://youtube.com/watch?v=unseen2",
            published=datetime(2023, 12, 22, 15, 0, 0, tzinfo=timezone.utc),
            seen=False
        ),
    ]
    
    # Create request
    req = RecommendRequest(items=items, limit=20)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify result structure
    assert isinstance(result, RecommendResult)
    assert isinstance(result.items, list)
    assert all(isinstance(item, Item) for item in result.items)
    
    # Verify content - should recommend unseen items with matching keywords
    assert len(result.items) == 2
    assert result.items[0].item_id == "youtube:unseen1"  # Python Guide (matches "python")
    assert result.items[1].item_id == "youtube:unseen2"  # JavaScript (no matching keywords, score=0)


def test_keyword_from_seen_recommender_meta_contains_recommender_info() -> None:
    """Test c) meta contains recommender information."""
    from tech_tracker.app.recommend import KeywordFromSeenRecommender
    
    recommender = KeywordFromSeenRecommender()
    
    # Create test items
    now = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="youtube:seen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="Python Programming",
            link="https://youtube.com/watch?v=seen1",
            published=now,
            seen=True
        ),
        Item(
            item_id="youtube:unseen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="Python Tutorial",
            link="https://youtube.com/watch?v=unseen1",
            published=datetime(2023, 12, 21, 15, 0, 0, tzinfo=timezone.utc),
            seen=False
        ),
    ]
    
    # Create request
    req = RecommendRequest(items=items, limit=10)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify meta contains recommender information
    assert isinstance(result.meta, dict)
    assert "strategy" in result.meta
    assert result.meta["strategy"] == "keyword_from_seen"
    assert "limit" in result.meta
    assert result.meta["limit"] == 10
    assert "total_items" in result.meta
    assert result.meta["total_items"] == 2


def test_keyword_from_seen_recommender_consistency_with_pure_function() -> None:
    """Test that recommender output matches pure function output."""
    from tech_tracker.app.recommend import KeywordFromSeenRecommender, recommend_keyword_from_seen
    
    recommender = KeywordFromSeenRecommender()
    
    # Create test items
    now = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="youtube:seen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="Python Programming Tutorial",
            link="https://youtube.com/watch?v=seen1",
            published=now,
            seen=True
        ),
        Item(
            item_id="youtube:seen2",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="JavaScript Guide",
            link="https://youtube.com/watch?v=seen2",
            published=datetime(2023, 12, 21, 15, 0, 0, tzinfo=timezone.utc),
            seen=True
        ),
        Item(
            item_id="youtube:unseen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/3",
            title="Python Advanced",
            link="https://youtube.com/watch?v=unseen1",
            published=datetime(2023, 12, 22, 15, 0, 0, tzinfo=timezone.utc),
            seen=False
        ),
        Item(
            item_id="youtube:unseen2",
            source_type="youtube",
            source_url="https://youtube.com/channel/4",
            title="JavaScript Tutorial",
            link="https://youtube.com/watch?v=unseen2",
            published=datetime(2023, 12, 23, 15, 0, 0, tzinfo=timezone.utc),
            seen=False
        ),
    ]
    
    # Get output from pure function
    pure_function_result = recommend_keyword_from_seen(items, limit=20)
    
    # Get output from recommender
    req = RecommendRequest(items=items, limit=20)
    recommender_result = recommender.recommend(req)
    
    # Verify they are equivalent
    assert len(pure_function_result) == len(recommender_result.items)
    for pure_item, recommender_item in zip(pure_function_result, recommender_result.items):
        assert pure_item.item_id == recommender_item.item_id
        assert pure_item.title == recommender_item.title
        assert pure_item.seen == recommender_item.seen


def test_keyword_from_seen_recommender_token_plus_support() -> None:
    """Test that tokenizer supports + sign within tokens like 'c++' and 'g++'."""
    from tech_tracker.app.recommend import KeywordFromSeenRecommender
    
    recommender = KeywordFromSeenRecommender()
    
    # Create test items with seen items containing + signs
    now = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="seen:csharp",
            source_type="youtube",
            source_url="https://youtube.com/channel/csharp",
            title="C# Programming Tutorial",
            link="https://youtube.com/watch?v=csharp",
            published=now,
            seen=True
        ),
        Item(
            item_id="seen:cplusplus",
            source_type="youtube", 
            source_url="https://youtube.com/channel/cpp",
            title="C++ Programming Guide",
            link="https://youtube.com/watch?v=cpp",
            published=datetime(2023, 12, 21, 15, 0, 0, tzinfo=timezone.utc),
            seen=True
        ),
        Item(
            item_id="unseen:cpp_project",
            source_type="youtube",
            source_url="https://youtube.com/channel/cpp_project",
            title="C++ Project Setup Tutorial",
            link="https://youtube.com/watch?v=cpp_project",
            published=datetime(2023, 12, 22, 15, 0, 0, tzinfo=timezone.utc),
            seen=False
        ),
        Item(
            item_id="unseen:gplus_project",
            source_type="youtube",
            source_url="https://youtube.com/channel/gplus",
            title="g++ Build System Guide",
            link="https://youtube.com/watch?v=gplus",
            published=datetime(2023, 12, 23, 15, 0, 0, tzinfo=timezone.utc),
            seen=False
        ),
        Item(
            item_id="unseen:java_project",
            source_type="youtube",
            source_url="https://youtube.com/channel/java",
            title="Java Programming Basics",
            link="https://youtube.com/watch?v=java",
            published=datetime(2023, 12, 24, 15, 0, 0, tzinfo=timezone.utc),
            seen=False
        ),
    ]
    
    # Create request
    req = RecommendRequest(items=items, limit=20)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify top_keywords field exists and contains expected tokens with + signs
    assert "top_keywords" in result.meta
    top_keywords = result.meta["top_keywords"]
    
    # Expected keywords with weights from seen items:
    # "c#": 1, "programming": 1, "tutorial": 1 (from "C# Programming Tutorial")
    # "c++": 1, "programming": 1, "guide": 1 (from "C++ Programming Guide")
    
    # Verify c++ and c# are recognized as single tokens
    keyword_dict = dict(top_keywords)
    assert "c++" in keyword_dict
    assert "c#" in keyword_dict
    assert keyword_dict["c++"] == 1
    assert keyword_dict["c#"] == 1
    
    # Verify recommendation results
    # Items with c++ should be ranked higher due to matching keywords
    recommended_ids = [item.item_id for item in result.items]
    
    # Both c++ and g++ items should be recommended before java item
    assert "unseen:cpp_project" in recommended_ids
    assert "unseen:gplus_project" in recommended_ids
    
    # Check that c++ item appears before java item (which has no matching keywords)
    cpp_index = recommended_ids.index("unseen:cpp_project")
    java_index = recommended_ids.index("unseen:java_project")
    assert cpp_index < java_index
    
    # Check that g++ item also appears before java item
    gplus_index = recommended_ids.index("unseen:gplus_project")
    assert gplus_index < java_index


def test_keyword_from_seen_recommender_top_keywords_meta() -> None:
    """Test that KeywordFromSeenRecommender includes top_keywords in meta."""
    from tech_tracker.app.recommend import KeywordFromSeenRecommender
    
    recommender = KeywordFromSeenRecommender()
    
    # Create test items with seen items containing various keywords
    now = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="seen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="Python Programming Tutorial",
            link="https://youtube.com/watch?v=seen1",
            published=now,
            seen=True
        ),
        Item(
            item_id="seen2",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="Advanced Python Guide",
            link="https://youtube.com/watch?v=seen2",
            published=datetime(2023, 12, 21, 15, 0, 0, tzinfo=timezone.utc),
            seen=True
        ),
        Item(
            item_id="seen3",
            source_type="youtube",
            source_url="https://youtube.com/channel/3",
            title="JavaScript Basics Tutorial",
            link="https://youtube.com/watch?v=seen3",
            published=datetime(2023, 12, 22, 15, 0, 0, tzinfo=timezone.utc),
            seen=True
        ),
        Item(
            item_id="unseen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/4",
            title="Python Advanced Techniques",
            link="https://youtube.com/watch?v=unseen1",
            published=datetime(2023, 12, 23, 15, 0, 0, tzinfo=timezone.utc),
            seen=False
        ),
    ]
    
    # Create request
    req = RecommendRequest(items=items, limit=20)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify top_keywords field exists in meta
    assert "top_keywords" in result.meta
    assert isinstance(result.meta["top_keywords"], list)
    
    # Verify keyword weights and sorting
    top_keywords = result.meta["top_keywords"]
        
        # Expected keywords and their counts (only from seen items):
    # "python": 2 (from "Python Programming Tutorial", "Advanced Python Guide")
    # "tutorial": 2 (from "Python Programming Tutorial", "JavaScript Basics Tutorial") 
    # "advanced": 1 (from "Advanced Python Guide")
    # "guide": 1, "programming": 1, "javascript": 1, "basics": 1
    
    # Verify the top keywords are correctly sorted by weight desc, then keyword asc
    expected_keywords = [
        ("python", 2),
        ("tutorial", 2),  # Same weight as "python", but "tutorial" comes after "python" alphabetically
        ("advanced", 1),
        ("basics", 1),
        ("guide", 1),
        ("javascript", 1),
        ("programming", 1),
    ]
    
    assert len(top_keywords) == len(expected_keywords)
    assert top_keywords == expected_keywords


def test_keyword_from_seen_recommender_top_keywords_no_seen_items() -> None:
    """Test top_keywords when no seen items exist."""
    from tech_tracker.app.recommend import KeywordFromSeenRecommender
    
    recommender = KeywordFromSeenRecommender()
    
    # Create test items with no seen items
    now = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="unseen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="Python Programming Tutorial",
            link="https://youtube.com/watch?v=unseen1",
            published=now,
            seen=False
        ),
        Item(
            item_id="unseen2",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="JavaScript Basics",
            link="https://youtube.com/watch?v=unseen2",
            published=datetime(2023, 12, 21, 15, 0, 0, tzinfo=timezone.utc),
            seen=False
        ),
    ]
    
    # Create request
    req = RecommendRequest(items=items, limit=20)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify top_keywords field exists and is empty list
    assert "top_keywords" in result.meta
    assert result.meta["top_keywords"] == []


def test_keyword_from_seen_recommender_top_keywords_empty_titles() -> None:
    """Test top_keywords when seen items have empty or non-tokenizable titles."""
    from tech_tracker.app.recommend import KeywordFromSeenRecommender
    
    recommender = KeywordFromSeenRecommender()
    
    # Create test items with seen items having empty titles or only punctuation
    now = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="seen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="!!!",  # Only punctuation, no tokens
            link="https://youtube.com/watch?v=seen1",
            published=now,
            seen=True
        ),
        Item(
            item_id="seen2",
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="",  # Empty title
            link="https://youtube.com/watch?v=seen2",
            published=datetime(2023, 12, 21, 15, 0, 0, tzinfo=timezone.utc),
            seen=True
        ),
        Item(
            item_id="unseen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/3",
            title="Python Tutorial",
            link="https://youtube.com/watch?v=unseen1",
            published=datetime(2023, 12, 22, 15, 0, 0, tzinfo=timezone.utc),
            seen=False
        ),
    ]
    
    # Create request
    req = RecommendRequest(items=items, limit=20)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify top_keywords field exists and is empty list (no extractable keywords)
    assert "top_keywords" in result.meta
    assert result.meta["top_keywords"] == []


def test_keyword_from_seen_recommender_top_keywords_tie_break_alphabetical() -> None:
    """Test that keywords with same weight are sorted alphabetically."""
    from tech_tracker.app.recommend import KeywordFromSeenRecommender
    
    recommender = KeywordFromSeenRecommender()
    
    # Create test items designed to create ties
    now = datetime(2023, 12, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = [
        Item(
            item_id="seen1",
            source_type="youtube",
            source_url="https://youtube.com/channel/1",
            title="zebra apple banana",  # Creates zebra, apple, banana each with count 1
            link="https://youtube.com/watch?v=seen1",
            published=now,
            seen=True
        ),
        Item(
            item_id="seen2", 
            source_type="youtube",
            source_url="https://youtube.com/channel/2",
            title="cherry dog",  # Creates cherry, dog each with count 1
            link="https://youtube.com/watch?v=seen2",
            published=datetime(2023, 12, 21, 15, 0, 0, tzinfo=timezone.utc),
            seen=True
        ),
    ]
    
    # Create request
    req = RecommendRequest(items=items, limit=20)
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Verify top_keywords field exists
    assert "top_keywords" in result.meta
    top_keywords = result.meta["top_keywords"]
    
    # All keywords have weight 1, should be sorted alphabetically
    expected_keywords = [
        ("apple", 1),
        ("banana", 1),
        ("cherry", 1),
        ("dog", 1),
        ("zebra", 1),
    ]
    
    assert len(top_keywords) == len(expected_keywords)
    assert top_keywords == expected_keywords
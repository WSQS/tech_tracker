"""Tests for render_recommendation_markdown function."""

from datetime import datetime, timezone

from tech_tracker.app.recommend import RecommendResult, render_recommendation_markdown
from tech_tracker.item import Item


def test_render_empty_recommendation() -> None:
    """Test a) items empty, meta empty: only output empty string."""
    result = RecommendResult(items=[], meta={})
    
    markdown = render_recommendation_markdown(result)
    
    expected = ""
    assert markdown == expected


def test_render_single_item_with_meta() -> None:
    """Test b) 1 item, meta with strategy/limit: complete rendering with title, meta, section, bullets, and trailing newline."""
    # Create test item
    published_time = datetime(2023, 12, 20, 10, 30, 45, tzinfo=timezone.utc)
    item = Item(
        item_id="test123",
        source_type="youtube",
        source_url="https://youtube.com/channel/testchannel",
        title="Test Video Title",
        link="https://youtube.com/watch?v=test123",
        published=published_time,
    )
    
    # Create result with meta
    result = RecommendResult(
        items=[item],
        meta={
            "strategy": "latest",
            "limit": 5,
            "extra": "ignored",  # Should be ignored
        }
    )
    
    markdown = render_recommendation_markdown(result)
    
    expected = """_Strategy_: latest
_Limit_: 5

## 1. Test Video Title
- ID: `test123`
- Source: youtube
- Channel: https://youtube.com/channel/testchannel
- Published: 2023-12-20T10:30:45Z
- Link: https://youtube.com/watch?v=test123

"""
    
    assert markdown == expected


def test_render_two_items_ordering() -> None:
    """Test c) 2 items: numbered 1/2, order matches result.items, with empty lines between sections."""
    # Create test items
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    item1 = Item(
        item_id="item1",
        source_type="youtube",
        source_url="https://youtube.com/channel/channel1",
        title="First Video",
        link="https://youtube.com/watch?v=item1",
        published=base_time,
    )
    
    item2 = Item(
        item_id="item2",
        source_type="rss",
        source_url="https://example.com/feed.xml",
        title="Second Article",
        link="https://example.com/article2",
        published=base_time.replace(hour=11),
    )
    
    # Create result with items in specific order
    result = RecommendResult(items=[item1, item2], meta={})
    
    markdown = render_recommendation_markdown(result)
    
    expected = """## 1. First Video
- ID: `item1`
- Source: youtube
- Channel: https://youtube.com/channel/channel1
- Published: 2023-12-20T10:00:00Z
- Link: https://youtube.com/watch?v=item1

## 2. Second Article
- ID: `item2`
- Source: rss
- Channel: https://example.com/feed.xml
- Published: 2023-12-20T11:00:00Z
- Link: https://example.com/article2

"""
    
    assert markdown == expected


def test_render_microseconds_in_published_time() -> None:
    """Test that microseconds are preserved in published time formatting."""
    # Create test item with microseconds
    published_time = datetime(2023, 12, 20, 10, 30, 45, 123456, tzinfo=timezone.utc)
    item = Item(
        item_id="micro123",
        source_type="youtube",
        source_url="https://youtube.com/channel/micro",
        title="Microsecond Video",
        link="https://youtube.com/watch?v=micro123",
        published=published_time,
    )
    
    result = RecommendResult(items=[item], meta={})
    
    markdown = render_recommendation_markdown(result)
    
    expected = """## 1. Microsecond Video
- ID: `micro123`
- Source: youtube
- Channel: https://youtube.com/channel/micro
- Published: 2023-12-20T10:30:45.123456Z
- Link: https://youtube.com/watch?v=micro123

"""
    
    assert markdown == expected


def test_render_partial_meta() -> None:
    """Test rendering with only strategy or only limit in meta."""
    # Create test item
    published_time = datetime(2023, 12, 20, 10, 30, 45, tzinfo=timezone.utc)
    item = Item(
        item_id="partial123",
        source_type="youtube",
        source_url="https://youtube.com/channel/partial",
        title="Partial Meta Video",
        link="https://youtube.com/watch?v=partial123",
        published=published_time,
    )
    
    # Test with only strategy
    result_strategy = RecommendResult(items=[item], meta={"strategy": "latest"})
    markdown_strategy = render_recommendation_markdown(result_strategy)
    
    expected_strategy = """_Strategy_: latest

## 1. Partial Meta Video
- ID: `partial123`
- Source: youtube
- Channel: https://youtube.com/channel/partial
- Published: 2023-12-20T10:30:45Z
- Link: https://youtube.com/watch?v=partial123

"""
    
    assert markdown_strategy == expected_strategy
    
    # Test with only limit
    result_limit = RecommendResult(items=[item], meta={"limit": 10})
    markdown_limit = render_recommendation_markdown(result_limit)
    
    expected_limit = """_Limit_: 10

## 1. Partial Meta Video
- ID: `partial123`
- Source: youtube
- Channel: https://youtube.com/channel/partial
- Published: 2023-12-20T10:30:45Z
- Link: https://youtube.com/watch?v=partial123

"""
    
    assert markdown_limit == expected_limit


def test_render_with_top_keywords_non_empty() -> None:
    """Test rendering with non-empty top_keywords for keyword_from_seen strategy."""
    # Create test item
    published_time = datetime(2023, 12, 20, 10, 30, 45, tzinfo=timezone.utc)
    item = Item(
        item_id="test123",
        source_type="youtube",
        source_url="https://youtube.com/channel/testchannel",
        title="Test Video",
        link="https://youtube.com/watch?v=test123",
        published=published_time,
    )
    
    # Create result with keyword_from_seen strategy and top_keywords
    result = RecommendResult(
        items=[item],
        meta={
            "strategy": "keyword_from_seen",
            "limit": 5,
            "top_keywords": [("python", 3), ("async", 1), ("tutorial", 2)]
        }
    )
    
    markdown = render_recommendation_markdown(result)
    
    expected = """_Strategy_: keyword_from_seen
_Limit_: 5
_Top keywords_: python(3), async(1), tutorial(2)

## 1. Test Video
- ID: `test123`
- Source: youtube
- Channel: https://youtube.com/channel/testchannel
- Published: 2023-12-20T10:30:45Z
- Link: https://youtube.com/watch?v=test123

"""
    
    assert markdown == expected


def test_render_with_top_keywords_empty() -> None:
    """Test rendering with empty top_keywords for keyword_from_seen strategy."""
    # Create test item
    published_time = datetime(2023, 12, 20, 10, 30, 45, tzinfo=timezone.utc)
    item = Item(
        item_id="test123",
        source_type="youtube",
        source_url="https://youtube.com/channel/testchannel",
        title="Test Video",
        link="https://youtube.com/watch?v=test123",
        published=published_time,
    )
    
    # Create result with keyword_from_seen strategy and empty top_keywords
    result = RecommendResult(
        items=[item],
        meta={
            "strategy": "keyword_from_seen",
            "limit": 5,
            "top_keywords": []
        }
    )
    
    markdown = render_recommendation_markdown(result)
    
    expected = """_Strategy_: keyword_from_seen
_Limit_: 5
_Top keywords_: (none)

## 1. Test Video
- ID: `test123`
- Source: youtube
- Channel: https://youtube.com/channel/testchannel
- Published: 2023-12-20T10:30:45Z
- Link: https://youtube.com/watch?v=test123

"""
    
    assert markdown == expected


def test_render_latest_strategy_without_top_keywords() -> None:
    """Test that latest strategy does not show top_keywords even if present."""
    # Create test item
    published_time = datetime(2023, 12, 20, 10, 30, 45, tzinfo=timezone.utc)
    item = Item(
        item_id="test123",
        source_type="youtube",
        source_url="https://youtube.com/channel/testchannel",
        title="Test Video",
        link="https://youtube.com/watch?v=test123",
        published=published_time,
    )
    
    # Create result with latest strategy (should not show top_keywords even if present)
    result = RecommendResult(
        items=[item],
        meta={
            "strategy": "latest",
            "limit": 5,
            "top_keywords": [("python", 3), ("async", 1)]  # Should be ignored
        }
    )
    
    markdown = render_recommendation_markdown(result)
    
    expected = """_Strategy_: latest
_Limit_: 5

## 1. Test Video
- ID: `test123`
- Source: youtube
- Channel: https://youtube.com/channel/testchannel
- Published: 2023-12-20T10:30:45Z
- Link: https://youtube.com/watch?v=test123

"""
    
    assert markdown == expected


def test_render_keyword_from_seen_without_top_keywords_field() -> None:
    """Test keyword_from_seen strategy without top_keywords field."""
    # Create test item
    published_time = datetime(2023, 12, 20, 10, 30, 45, tzinfo=timezone.utc)
    item = Item(
        item_id="test123",
        source_type="youtube",
        source_url="https://youtube.com/channel/testchannel",
        title="Test Video",
        link="https://youtube.com/watch?v=test123",
        published=published_time,
    )
    
    # Create result with keyword_from_seen strategy but no top_keywords field
    result = RecommendResult(
        items=[item],
        meta={
            "strategy": "keyword_from_seen",
            "limit": 5
            # No top_keywords field
        }
    )
    
    markdown = render_recommendation_markdown(result)
    
    expected = """_Strategy_: keyword_from_seen
_Limit_: 5

## 1. Test Video
- ID: `test123`
- Source: youtube
- Channel: https://youtube.com/channel/testchannel
- Published: 2023-12-20T10:30:45Z
- Link: https://youtube.com/watch?v=test123

"""
    
    assert markdown == expected
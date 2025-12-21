"""Tests for render_recommendation_markdown function."""

from datetime import datetime, timezone

from tech_tracker.app.recommend import RecommendResult, render_recommendation_markdown
from tech_tracker.item import Item


def test_render_empty_recommendation() -> None:
    """Test a) items empty, meta empty: only output '# Recommended Items\n\n'."""
    result = RecommendResult(items=[], meta={})
    
    markdown = render_recommendation_markdown(result)
    
    expected = "# Recommended Items\n\n"
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
    
    expected = """# Recommended Items

_Strategy_: latest
_Limit_: 5

## 1. Test Video Title
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
    
    expected = """# Recommended Items

## 1. First Video
- Source: youtube
- Channel: https://youtube.com/channel/channel1
- Published: 2023-12-20T10:00:00Z
- Link: https://youtube.com/watch?v=item1

## 2. Second Article
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
    
    expected = """# Recommended Items

## 1. Microsecond Video
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
    
    expected_strategy = """# Recommended Items

_Strategy_: latest

## 1. Partial Meta Video
- Source: youtube
- Channel: https://youtube.com/channel/partial
- Published: 2023-12-20T10:30:45Z
- Link: https://youtube.com/watch?v=partial123

"""
    
    assert markdown_strategy == expected_strategy
    
    # Test with only limit
    result_limit = RecommendResult(items=[item], meta={"limit": 10})
    markdown_limit = render_recommendation_markdown(result_limit)
    
    expected_limit = """# Recommended Items

_Limit_: 10

## 1. Partial Meta Video
- Source: youtube
- Channel: https://youtube.com/channel/partial
- Published: 2023-12-20T10:30:45Z
- Link: https://youtube.com/watch?v=partial123

"""
    
    assert markdown_limit == expected_limit
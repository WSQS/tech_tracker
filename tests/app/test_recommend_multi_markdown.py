"""Tests for render_multi_recommendation_markdown function."""

from datetime import datetime, timezone

from tech_tracker.app.recommend import (
    RecommendResult, 
    render_multi_recommendation_markdown,
    LatestRecommender,
    KeywordFromSeenRecommender,
    RecommendRequest
)
from tech_tracker.item import Item


def test_render_multi_section_basic() -> None:
    """Test basic multi-section rendering with main title and section titles."""
    # Create test items
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    
    latest_item = Item(
        item_id="latest:123",
        source_type="youtube",
        source_url="https://youtube.com/channel/latest",
        title="Latest Video",
        link="https://youtube.com/watch?v=latest123",
        published=base_time,
        seen=False
    )
    
    keyword_item = Item(
        item_id="keyword:456",
        source_type="youtube",
        source_url="https://youtube.com/channel/keyword",
        title="Keyword Video",
        link="https://youtube.com/watch?v=keyword456",
        published=base_time.replace(hour=11),
        seen=False
    )
    
    # Create recommendation results
    latest_result = RecommendResult(
        items=[latest_item],
        meta={"strategy": "latest", "limit": 20}
    )
    
    keyword_result = RecommendResult(
        items=[keyword_item],
        meta={"strategy": "keyword_from_seen", "limit": 20}
    )
    
    # Render multi-section markdown
    sections = [
        ("Latest", latest_result),
        ("Keyword from Seen", keyword_result)
    ]
    
    markdown = render_multi_recommendation_markdown(sections)
    
    # Verify structure
    lines = markdown.split("\n")
    
    # 1) Main title exists and appears only once
    assert lines[0] == "# Recommended Items"
    assert lines.count("# Recommended Items") == 1
    
    # 2) Section titles appear in order
    assert "## Latest" in markdown
    assert "## Keyword from Seen" in markdown
    assert markdown.index("## Latest") < markdown.index("## Keyword from Seen")
    
    # 3) Each section contains its unique content
    assert "latest:123" in markdown
    assert "keyword:456" in markdown
    
    # 4) Verify section-specific content
    assert "_Strategy_: latest" in markdown
    assert "_Strategy_: keyword_from_seen" in markdown


def test_render_multi_section_empty_result() -> None:
    """Test rendering with empty RecommendResult."""
    # Create sections with empty and non-empty results
    empty_result = RecommendResult(items=[], meta={})
    
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    item = Item(
        item_id="test123",
        source_type="youtube",
        source_url="https://youtube.com/channel/test",
        title="Test Video",
        link="https://youtube.com/watch?v=test123",
        published=base_time,
        seen=False
    )
    
    non_empty_result = RecommendResult(
        items=[item],
        meta={"strategy": "latest", "limit": 10}
    )
    
    sections = [
        ("Empty Section", empty_result),
        ("Non-empty Section", non_empty_result)
    ]
    
    markdown = render_multi_recommendation_markdown(sections)
    
    # Verify both section titles appear
    assert "## Empty Section" in markdown
    assert "## Non-empty Section" in markdown
    
    # Verify empty section has no body content
    empty_section_start = markdown.find("## Empty Section")
    non_empty_section_start = markdown.find("## Non-empty Section")
    
    # Extract empty section content
    empty_section_content = markdown[empty_section_start:non_empty_section_start]
    # Should only contain the title and possibly empty lines
    assert "test123" not in empty_section_content
    
    # Verify non-empty section has content
    assert "test123" in markdown


def test_render_multi_section_meta_only() -> None:
    """Test rendering with meta-only RecommendResult."""
    # Create sections with meta-only results
    meta_only_result = RecommendResult(items=[], meta={"strategy": "latest", "limit": 5})
    
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    item = Item(
        item_id="test123",
        source_type="youtube",
        source_url="https://youtube.com/channel/test",
        title="Test Video",
        link="https://youtube.com/watch?v=test123",
        published=base_time,
        seen=False
    )
    
    item_result = RecommendResult(
        items=[item],
        meta={"strategy": "keyword_from_seen", "limit": 10}
    )
    
    sections = [
        ("Meta Only", meta_only_result),
        ("With Items", item_result)
    ]
    
    markdown = render_multi_recommendation_markdown(sections)
    
    # Verify meta-only section contains meta information
    assert "_Strategy_: latest" in markdown
    assert "_Limit_: 5" in markdown
    
    # Verify section with items contains both meta and item info
    assert "_Strategy_: keyword_from_seen" in markdown
    assert "test123" in markdown


def test_render_multi_section_ordering() -> None:
    """Test that sections are rendered in the provided order."""
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    
    # Create items with distinct IDs
    item1 = Item(
        item_id="first:123",
        source_type="youtube",
        source_url="https://youtube.com/channel/first",
        title="First Video",
        link="https://youtube.com/watch?v=first123",
        published=base_time,
        seen=False
    )
    
    item2 = Item(
        item_id="second:456",
        source_type="youtube",
        source_url="https://youtube.com/channel/second",
        title="Second Video",
        link="https://youtube.com/watch?v=second456",
        published=base_time.replace(hour=1),
        seen=False
    )
    
    item3 = Item(
        item_id="third:789",
        source_type="youtube",
        source_url="https://youtube.com/channel/third",
        title="Third Video",
        link="https://youtube.com/watch?v=third789",
        published=base_time.replace(hour=2),
        seen=False
    )
    
    # Create results
    result1 = RecommendResult(items=[item1], meta={"strategy": "first"})
    result2 = RecommendResult(items=[item2], meta={"strategy": "second"})
    result3 = RecommendResult(items=[item3], meta={"strategy": "third"})
    
    # Test different ordering
    sections = [
        ("Third Section", result3),
        ("First Section", result1),
        ("Second Section", result2)
    ]
    
    markdown = render_multi_recommendation_markdown(sections)
    
    # Verify sections appear in the specified order
    third_pos = markdown.find("## Third Section")
    first_pos = markdown.find("## First Section")
    second_pos = markdown.find("## Second Section")
    
    assert third_pos < first_pos < second_pos
    
    # Verify content follows section order
    third_content_pos = markdown.find("third:789")
    first_content_pos = markdown.find("first:123")
    second_content_pos = markdown.find("second:456")
    
    assert third_content_pos < first_content_pos < second_content_pos


def test_render_multi_section_with_real_recommenders() -> None:
    """Test multi-section rendering with actual recommender outputs."""
    # Create test items
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    
    seen_item = Item(
        item_id="seen:123",
        source_type="youtube",
        source_url="https://youtube.com/channel/seen",
        title="Python Programming",
        link="https://youtube.com/watch?v=seen123",
        published=base_time,
        seen=True
    )
    
    unseen_item1 = Item(
        item_id="unseen1:456",
        source_type="youtube",
        source_url="https://youtube.com/channel/unseen1",
        title="Advanced Python",
        link="https://youtube.com/watch?v=unseen1456",
        published=base_time.replace(hour=1),
        seen=False
    )
    
    unseen_item2 = Item(
        item_id="unseen2:789",
        source_type="youtube",
        source_url="https://youtube.com/channel/unseen2",
        title="JavaScript Tutorial",
        link="https://youtube.com/watch?v=unseen2789",
        published=base_time.replace(hour=2),
        seen=False
    )
    
    items = [seen_item, unseen_item1, unseen_item2]
    
    # Get recommendations from actual recommenders
    latest_recommender = LatestRecommender()
    keyword_recommender = KeywordFromSeenRecommender()
    
    req = RecommendRequest(items=items, limit=20)
    
    latest_result = latest_recommender.recommend(req)
    keyword_result = keyword_recommender.recommend(req)
    
    # Render multi-section markdown
    sections = [
        ("Latest", latest_result),
        ("Keyword from Seen", keyword_result)
    ]
    
    markdown = render_multi_recommendation_markdown(sections)
    
    # Verify structure
    assert "# Recommended Items" in markdown
    assert "## Latest" in markdown
    assert "## Keyword from Seen" in markdown
    
    # Verify content from both recommenders
    assert "unseen1:456" in markdown  # Should appear in both (latest and keyword)
    assert "unseen2:789" in markdown  # Should appear in both (latest and keyword)
    # Note: seen:123 appears in latest (fallback) but not in keyword recommender
    
    # Verify meta information
    assert "_Strategy_: latest" in markdown
    assert "_Strategy_: keyword_from_seen" in markdown


def test_render_multi_section_empty_sections_list() -> None:
    """Test rendering with empty sections list."""
    markdown = render_multi_recommendation_markdown([])
    
    # Should only contain main title and trailing newline
    expected = "# Recommended Items\n"
    assert markdown == expected


def test_render_multi_section_single_section() -> None:
    """Test rendering with single section."""
    base_time = datetime(2023, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
    
    item = Item(
        item_id="single:123",
        source_type="youtube",
        source_url="https://youtube.com/channel/single",
        title="Single Video",
        link="https://youtube.com/watch?v=single123",
        published=base_time,
        seen=False
    )
    
    result = RecommendResult(
        items=[item],
        meta={"strategy": "latest", "limit": 10}
    )
    
    sections = [("Single Section", result)]
    
    markdown = render_multi_recommendation_markdown(sections)
    
    # Verify structure
    assert markdown.startswith("# Recommended Items\n\n## Single Section")
    assert "single:123" in markdown
    assert "_Strategy_: latest" in markdown
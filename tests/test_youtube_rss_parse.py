"""Tests for YouTube RSS feed parser."""

from datetime import datetime, timezone

import pytest

from tech_tracker.youtube_rss import parse_youtube_feed


# Sample YouTube RSS feed XML with 2 entries
YOUTUBE_FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" 
      xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
  <id>yt:channel:UC1234567890</id>
  <title>Test Channel</title>
  <link rel="alternate" href="https://www.youtube.com/channel/UC1234567890"/>
  <updated>2023-12-20T10:00:00+00:00</updated>
  
  <entry>
    <yt:videoId>abc123def456</yt:videoId>
    <title>First Video Title</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123def456"/>
    <published>2023-12-20T09:00:00Z</published>
    <updated>2023-12-20T09:00:00Z</updated>
  </entry>
  
  <entry>
    <yt:videoId>xyz789uvw012</yt:videoId>
    <title>Second Video Title</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=xyz789uvw012"/>
    <published>2023-12-19T15:30:00Z</published>
    <updated>2023-12-19T15:30:00Z</updated>
  </entry>
</feed>"""


# Empty feed XML
EMPTY_FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" 
      xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
  <id>yt:channel:UC1234567890</id>
  <title>Test Channel</title>
  <link rel="alternate" href="https://www.youtube.com/channel/UC1234567890"/>
  <updated>2023-12-20T10:00:00+00:00</updated>
</feed>"""


# Malformed XML
MALFORMED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015">
  <id>yt:channel:UC1234567890</id>
  <title>Test Channel</title>
  <link rel="alternate" href="https://www.youtube.com/channel/UC1234567890"/>
  <updated>2023-12-20T10:00:00+00:00</updated>
  
  <entry>
    <yt:videoId>abc123def456</yt:videoId>
    <title>First Video Title</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123def456"/>
    <published>2023-12-20T09:00:00Z</published>
  </entry>
  
  <unclosed_tag>
</feed>"""


def test_parse_youtube_feed_normal() -> None:
    """Test normal parsing of YouTube feed with 2 entries."""
    videos = parse_youtube_feed(YOUTUBE_FEED_XML)
    
    # Check length
    assert len(videos) == 2
    
    # Check first video
    first_video = videos[0]
    assert first_video["video_id"] == "abc123def456"
    assert first_video["title"] == "First Video Title"
    assert first_video["link"] == "https://www.youtube.com/watch?v=abc123def456"
    
    # Check published date is timezone-aware and in UTC
    published = first_video["published"]
    assert isinstance(published, datetime)
    assert published.tzinfo is not None
    assert published.tzinfo == timezone.utc
    assert published == datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc)
    
    # Check second video
    second_video = videos[1]
    assert second_video["video_id"] == "xyz789uvw012"
    assert second_video["title"] == "Second Video Title"
    assert second_video["link"] == "https://www.youtube.com/watch?v=xyz789uvw012"
    
    # Check published date is timezone-aware and in UTC
    published = second_video["published"]
    assert isinstance(published, datetime)
    assert published.tzinfo is not None
    assert published.tzinfo == timezone.utc
    assert published == datetime(2023, 12, 19, 15, 30, 0, tzinfo=timezone.utc)


def test_parse_youtube_feed_empty() -> None:
    """Test parsing empty feed returns empty list."""
    videos = parse_youtube_feed(EMPTY_FEED_XML)
    assert videos == []


def test_parse_youtube_feed_empty_string() -> None:
    """Test parsing empty string returns empty list."""
    videos = parse_youtube_feed("")
    assert videos == []


def test_parse_youtube_feed_whitespace_only() -> None:
    """Test parsing whitespace-only string returns empty list."""
    videos = parse_youtube_feed("   \n\t  ")
    assert videos == []


def test_parse_youtube_feed_malformed_xml() -> None:
    """Test parsing malformed XML raises ValueError."""
    with pytest.raises(ValueError, match="Failed to parse XML"):
        parse_youtube_feed(MALFORMED_XML)


def test_parse_youtube_feed_partial_missing_fields() -> None:
    """Test feed with entries missing some fields."""
    partial_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" 
      xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <yt:videoId>abc123def456</yt:videoId>
    <title>Complete Video</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123def456"/>
    <published>2023-12-20T09:00:00Z</published>
  </entry>
  
  <entry>
    <!-- Missing video_id -->
    <title>Incomplete Video</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=missing"/>
    <published>2023-12-20T10:00:00Z</published>
  </entry>
  
  <entry>
    <yt:videoId>xyz789uvw012</yt:videoId>
    <!-- Missing title -->
    <link rel="alternate" href="https://www.youtube.com/watch?v=xyz789uvw012"/>
    <published>2023-12-20T11:00:00Z</published>
  </entry>
  
  <entry>
    <yt:videoId>def456ghi789</yt:videoId>
    <title>Another Complete Video</title>
    <!-- Missing link -->
    <published>2023-12-20T12:00:00Z</published>
  </entry>
  
  <entry>
    <yt:videoId>ghi789jkl012</yt:videoId>
    <title>Video with Invalid Date</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=ghi789jkl012"/>
    <published>invalid-date</published>
  </entry>
</feed>"""
    
    videos = parse_youtube_feed(partial_xml)
    
    # Only the complete entry should be parsed
    assert len(videos) == 1
    assert videos[0]["video_id"] == "abc123def456"
    assert videos[0]["title"] == "Complete Video"
    assert videos[0]["link"] == "https://www.youtube.com/watch?v=abc123def456"


def test_parse_youtube_feed_different_link_formats() -> None:
    """Test feed with different link formats."""
    link_test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" 
      xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <yt:videoId>abc123def456</yt:videoId>
    <title>Video with alternate link</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123def456"/>
    <link href="https://other-link.com"/>
    <published>2023-12-20T09:00:00Z</published>
  </entry>
  
  <entry>
    <yt:videoId>xyz789uvw012</yt:videoId>
    <title>Video with regular link</title>
    <link href="https://www.youtube.com/watch?v=xyz789uvw012"/>
    <published>2023-12-20T10:00:00Z</published>
  </entry>
</feed>"""
    
    videos = parse_youtube_feed(link_test_xml)
    
    assert len(videos) == 2
    
    # First video should use alternate link
    assert videos[0]["link"] == "https://www.youtube.com/watch?v=abc123def456"
    
    # Second video should use regular link
    assert videos[1]["link"] == "https://www.youtube.com/watch?v=xyz789uvw012"


def test_parse_youtube_feed_timezone_handling() -> None:
    """Test proper timezone handling for published dates."""
    timezone_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" 
      xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <yt:videoId>abc123def456</yt:videoId>
    <title>Video with Z timezone</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123def456"/>
    <published>2023-12-20T09:00:00Z</published>
  </entry>
  
  <entry>
    <yt:videoId>xyz789uvw012</yt:videoId>
    <title>Video with explicit timezone</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=xyz789uvw012"/>
    <published>2023-12-20T10:00:00+02:00</published>
  </entry>
</feed>"""
    
    videos = parse_youtube_feed(timezone_xml)
    
    assert len(videos) == 2
    
    # First video: Z timezone should convert to UTC
    assert videos[0]["published"] == datetime(2023, 12, 20, 9, 0, 0, tzinfo=timezone.utc)
    
    # Second video: +02:00 should convert to UTC (10:00 +02:00 = 08:00 UTC)
    assert videos[1]["published"] == datetime(2023, 12, 20, 8, 0, 0, tzinfo=timezone.utc)
"""Compatibility layer for YouTube RSS functionality.

This module provides backward compatibility by re-exporting symbols
from the new location at tech_tracker.sources.youtube.
"""

# Re-export all public symbols from the new location
from tech_tracker.sources.youtube.rss import (
    parse_youtube_feed,
    build_youtube_feed_url,
)

__all__ = [
    "parse_youtube_feed",
    "build_youtube_feed_url",
]
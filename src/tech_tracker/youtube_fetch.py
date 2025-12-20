"""Compatibility layer for YouTube fetch functionality.

This module provides backward compatibility by re-exporting symbols
from the new location at tech_tracker.sources.youtube.
"""

# Re-export all public symbols from the new location
from tech_tracker.sources.youtube.fetch import (
    fetch_youtube_videos,
)

__all__ = [
    "fetch_youtube_videos",
]
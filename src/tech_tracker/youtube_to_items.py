"""Compatibility layer for YouTube to items functionality.

This module provides backward compatibility by re-exporting symbols
from the new location at tech_tracker.sources.youtube.
"""

# Re-export all public symbols from the new location
from tech_tracker.sources.youtube.to_items import (
    youtube_videos_to_items,
)

__all__ = [
    "youtube_videos_to_items",
]
"""Compatibility layer for app YouTube functionality.

This module provides backward compatibility by re-exporting symbols
from the new location at tech_tracker.app.
"""

# Re-export all public symbols from the new location
from tech_tracker.app.youtube import (
    fetch_youtube_videos_from_config,
)

__all__ = [
    "fetch_youtube_videos_from_config",
]
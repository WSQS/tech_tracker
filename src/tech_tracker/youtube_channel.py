"""Compatibility layer for YouTube channel functionality.

This module provides backward compatibility by re-exporting symbols
from the new location at tech_tracker.sources.youtube.
"""

# Re-export all public symbols from the new location
from tech_tracker.sources.youtube.channel import (
    extract_channel_id_from_youtube_url,
)

__all__ = [
    "extract_channel_id_from_youtube_url",
]
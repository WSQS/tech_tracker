"""Compatibility layer for app update functionality.

This module provides backward compatibility by re-exporting symbols
from the new location at tech_tracker.app.
"""

# Re-export all public symbols from the new location
from tech_tracker.app.update import (
    fetch_youtube_new_items,
)

__all__ = [
    "fetch_youtube_new_items",
]
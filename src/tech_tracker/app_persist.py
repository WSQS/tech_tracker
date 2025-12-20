"""Compatibility layer for app persist functionality.

This module provides backward compatibility by re-exporting symbols
from the new location at tech_tracker.app.
"""

# Re-export all public symbols from the new location
from tech_tracker.app.persist import (
    fetch_and_persist_youtube_items,
)

__all__ = [
    "fetch_and_persist_youtube_items",
]
"""Item ID utilities for creating namespaced unique identifiers.

This module provides utilities for creating consistent, namespaced item IDs
across different source types to ensure global uniqueness.
"""

from typing import Final


# Source type constants
SOURCE_TYPE_YOUTUBE: Final[str] = "youtube"
SOURCE_TYPE_RSS: Final[str] = "rss"
SOURCE_TYPE_BILIBILI: Final[str] = "bilibili"


def build_item_id(source_type: str, source_item_id: str) -> str:
    """Build a namespaced item ID.
    
    Args:
        source_type: The type of source (e.g., "youtube", "rss", "bilibili")
        source_item_id: The original item ID from the source
        
    Returns:
        A namespaced item ID in the format "{source_type}:{source_item_id}"
        
    Examples:
        >>> build_item_id("youtube", "abc123")
        'youtube:abc123'
        >>> build_item_id("rss", "post-456")
        'rss:post-456'
    """
    if not source_type:
        raise ValueError("source_type cannot be empty")
    if not source_item_id:
        raise ValueError("source_item_id cannot be empty")
    if ":" in source_type:
        raise ValueError("source_type cannot contain ':' character")
    if ":" in source_item_id:
        raise ValueError("source_item_id cannot contain ':' character")
    
    return f"{source_type}:{source_item_id}"


def parse_item_id(item_id: str) -> tuple[str, str]:
    """Parse a namespaced item ID back into source type and source item ID.
    
    Args:
        item_id: A namespaced item ID in the format "{source_type}:{source_item_id}"
        
    Returns:
        A tuple of (source_type, source_item_id)
        
    Raises:
        ValueError: If the item_id is not in the expected format
        
    Examples:
        >>> parse_item_id("youtube:abc123")
        ('youtube', 'abc123')
    """
    if ":" not in item_id:
        raise ValueError(f"item_id '{item_id}' is not in the expected format 'source_type:source_item_id'")
    
    parts = item_id.split(":", 1)  # Split only on first colon
    if len(parts) != 2:
        raise ValueError(f"item_id '{item_id}' is not in the expected format 'source_type:source_item_id'")
    
    source_type, source_item_id = parts
    
    if not source_type:
        raise ValueError(f"item_id '{item_id}' has empty source_type")
    if not source_item_id:
        raise ValueError(f"item_id '{item_id}' has empty source_item_id")
    
    return source_type, source_item_id
"""Item diff utilities."""

from typing import Any, Dict, List


def diff_new_items(
    old_items: List[Dict[str, Any]], 
    new_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Find new items that don't exist in the old items.
    
    Args:
        old_items: List of existing items.
        new_items: List of new items to check.
        
    Returns:
        List of items from new_items whose item_id is not in old_items.
        Preserves the order from new_items.
    """
    # Create a set of existing item IDs for efficient lookup
    existing_ids = {item.get("item_id") for item in old_items if item.get("item_id")}
    
    # Find items with new IDs
    new_only_items = [
        item for item in new_items 
        if item.get("item_id") and item.get("item_id") not in existing_ids
    ]
    
    return new_only_items
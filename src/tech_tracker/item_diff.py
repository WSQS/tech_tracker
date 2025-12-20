"""Item diff utilities."""

from typing import Any, Dict, List, Union

from tech_tracker.item import Item


def diff_new_items(
    old_items: List[Union[Item, Dict[str, Any]]], 
    new_items: List[Union[Item, Dict[str, Any]]]
) -> List[Union[Item, Dict[str, Any]]]:
    """Find new items that don't exist in the old items.
    
    Args:
        old_items: List of existing items.
        new_items: List of new items to check.
        
    Returns:
        List of items from new_items whose item_id is not in old_items.
        Preserves the order from new_items.
    """
    # Create a set of existing item IDs for efficient lookup
    existing_ids = {
        item.item_id if isinstance(item, Item) else item.get("item_id") 
        for item in old_items 
        if (item.item_id if isinstance(item, Item) else item.get("item_id"))
    }
    
    # Find items with new IDs, preserving the original type
    new_only_items = []
    for item in new_items:
        item_id = item.item_id if isinstance(item, Item) else item.get("item_id")
        if item_id and item_id not in existing_ids:
            new_only_items.append(item)
    
    return new_only_items
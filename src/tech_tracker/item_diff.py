"""Item diff utilities."""

from typing import List

from tech_tracker.item import Item


def diff_new_items(
    old_items: List[Item], 
    new_items: List[Item]
) -> List[Item]:
    """Find new items that don't exist in the old items.
    
    Args:
        old_items: List of existing Item objects.
        new_items: List of new Item objects to check.
        
    Returns:
        List of Item objects from new_items whose item_id is not in old_items.
        Preserves the order from new_items.
    """
    # Create a set of existing item IDs for efficient lookup
    existing_ids = {item.item_id for item in old_items}
    
    # Find items with new IDs
    new_only_items = [
        item for item in new_items 
        if item.item_id not in existing_ids
    ]
    
    return new_only_items
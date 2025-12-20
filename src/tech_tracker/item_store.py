"""Item persistence layer using JSON file storage."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Union

from .item import Item


class JsonItemStore:
    """JSON file-based item storage.
    
    Stores items in a JSON file with the following structure:
    {"items": [item_dict, ...]}
    """
    
    def __init__(self, path: Union[str, Path]) -> None:
        """Initialize the store with a file path.
        
        Args:
            path: Path to the JSON file for storage.
        """
        self.path = Path(path)
    
    def load_all(self) -> List["Item"]:
        """Load all items from the JSON file.
        
        Returns:
            List of Item objects. Empty list if file doesn't exist.
            
        Raises:
            ValueError: If JSON is malformed or structure is invalid.
        """
        if not self.path.exists():
            return []
        
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.path}: {e}") from e
        
        if not isinstance(data, dict) or "items" not in data:
            raise ValueError(f"Invalid structure in {self.path}: missing 'items' key")
        
        items = data["items"]
        if not isinstance(items, list):
            raise ValueError(f"Invalid structure in {self.path}: 'items' must be a list")
        
        # Convert dicts to Item objects
        result = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"Invalid item in {self.path}: item must be a dictionary")
            
            try:
                # Convert dict to Item using Item.from_dict
                item_obj = Item.from_dict(item)
                result.append(item_obj)
            except ValueError as e:
                # Preserve original error message for timestamp validation
                if "Invalid datetime format" in str(e) or "Published datetime must end with 'Z'" in str(e):
                    raise ValueError(f"Invalid published timestamp in {self.path}: {e}") from e
                else:
                    raise ValueError(f"Invalid item data in {self.path}: {e}") from e
            except (KeyError, TypeError) as e:
                raise ValueError(f"Invalid item data in {self.path}: {e}") from e
        
        return result
    
    def save_many(self, items: List[Union["Item", Dict[str, Any]]]) -> None:
        """Save items to the JSON file, merging with existing items.
        
        Items are deduplicated by item_id. If an item_id already exists,
        the new item overwrites the old one.
        
        Args:
            items: List of Item objects or item dictionaries to save.
        """
        # Load existing items
        existing_items = {}
        try:
            for item in self.load_all():
                existing_items[item.item_id] = item
        except ValueError:
            # If we can't load existing items, start fresh
            existing_items = {}
        
        # Merge new items
        for item in items:
            # Handle both Item objects and dictionaries
            if isinstance(item, Item):
                item_obj = item
                item_id = item_obj.item_id
            else:
                # It's a dictionary
                item_id = item.get("item_id")
                if not item_id:
                    continue  # Skip items without item_id
                
                try:
                    item_obj = Item.from_dict(item)
                except (ValueError, TypeError) as e:
                    # Skip invalid items but continue processing others
                    continue
            
            existing_items[item_id] = item_obj
        
        # Sort items by published descending, then item_id ascending
        # Use Item objects for sorting to leverage their datetime fields
        sorted_items = sorted(
            existing_items.values(),
            key=lambda x: (-x.published.timestamp(), x.item_id)
        )
        
        # Convert Item objects back to dicts for JSON serialization
        dict_items = [item.to_dict() for item in sorted_items]
        
        # Save to file
        data = {"items": dict_items}
        
        # Ensure parent directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
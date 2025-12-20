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
    
    def load_all(self) -> List[Dict[str, Any]]:
        """Load all items from the JSON file.
        
        Returns:
            List of item dictionaries. Empty list if file doesn't exist.
            
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
        
        # Convert dicts to Item objects, then back to dicts for external interface
        result = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"Invalid item in {self.path}: item must be a dictionary")
            
            # Check if item has all required fields for Item.from_dict
            required_fields = ["item_id", "source_type", "source_url", "title", "link", "published"]
            has_all_fields = all(field in item for field in required_fields)
            
            if has_all_fields:
                try:
                    # Convert dict to Item using Item.from_dict
                    item_obj = Item.from_dict(item)
                    # Convert back to dict but keep published as datetime for external interface compatibility
                    item_dict = item_obj.to_dict()
                    # Convert published string back to datetime to maintain external interface
                    if "published" in item_dict:
                        item_dict["published"] = item_obj.published
                    result.append(item_dict)
                except ValueError as e:
                    # Preserve original error message for timestamp validation
                    if "Invalid datetime format" in str(e) or "Published datetime must end with 'Z'" in str(e):
                        raise ValueError(f"Invalid published timestamp in {self.path}: {e}") from e
                    else:
                        raise ValueError(f"Invalid item data in {self.path}: {e}") from e
            else:
                # For items without all required fields, we can't use Item dataclass
                # This maintains compatibility with existing tests that use partial items
                # Make a copy to avoid modifying original
                item_copy = dict(item)
                
                # Convert published timestamp back to datetime if present
                if "published" in item_copy and item_copy["published"]:
                    try:
                        # Use the same parsing logic as Item.from_dict for published field
                        published_raw = item_copy["published"]
                        if isinstance(published_raw, str):
                            if not published_raw.endswith("Z"):
                                raise ValueError(f"Published datetime must end with 'Z': {published_raw}")
                            published_str = published_raw[:-1] + "+00:00"
                            item_copy["published"] = datetime.fromisoformat(published_str).astimezone(timezone.utc)
                    except ValueError as e:
                        raise ValueError(f"Invalid published timestamp in {self.path}: {e}") from e
                
                result.append(item_copy)
        
        return result
    
    def save_many(self, items: List[Dict[str, Any]]) -> None:
        """Save items to the JSON file, merging with existing items.
        
        Items are deduplicated by item_id. If an item_id already exists,
        the new item overwrites the old one.
        
        Args:
            items: List of item dictionaries to save.
        """
        # Load existing items
        existing_items = {}
        try:
            for item in self.load_all():
                item_id = item.get("item_id")
                if item_id:
                    existing_items[item_id] = Item.from_dict(item)
        except ValueError:
            # If we can't load existing items, start fresh
            existing_items = {}
        
        # Merge new items
        for item in items:
            item_id = item.get("item_id")
            if not item_id:
                continue  # Skip items without item_id
            
            # Convert dict to Item using Item.from_dict
            try:
                item_obj = Item.from_dict(item)
                existing_items[item_id] = item_obj
            except (ValueError, TypeError) as e:
                # Skip invalid items but continue processing others
                continue
        
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
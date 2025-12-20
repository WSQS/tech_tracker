"""Item persistence layer using JSON file storage."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Union


def _dt_to_str(dt: datetime) -> str:
    """Convert datetime to ISO string with 'Z' suffix for UTC.
    
    Args:
        dt: Datetime object (should be timezone-aware).
        
    Returns:
        ISO string with 'Z' suffix.
    """
    # Ensure UTC and format with 'Z' suffix
    utc_time = dt.astimezone(timezone.utc)
    return utc_time.isoformat().replace("+00:00", "Z")


def _str_to_dt(s: str) -> datetime:
    """Convert ISO string to datetime (timezone-aware UTC).
    
    Args:
        s: ISO string with 'Z' suffix or '+00:00'.
        
    Returns:
        Timezone-aware datetime in UTC.
    """
    # Handle 'Z' suffix
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    
    dt = datetime.fromisoformat(s)
    
    # Ensure timezone-aware and in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    
    return dt


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
        
        # Convert string timestamps back to datetime objects
        result = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"Invalid item in {self.path}: item must be a dictionary")
            
            # Make a copy to avoid modifying original
            item_copy = dict(item)
            
            # Convert published timestamp back to datetime
            if "published" in item_copy and item_copy["published"]:
                try:
                    item_copy["published"] = _str_to_dt(item_copy["published"])
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
                    existing_items[item_id] = item
        except ValueError:
            # If we can't load existing items, start fresh
            existing_items = {}
        
        # Merge new items
        for item in items:
            item_id = item.get("item_id")
            if not item_id:
                continue  # Skip items without item_id
            
            # Make a copy to avoid modifying original
            item_copy = dict(item)
            
            # Convert datetime to string for JSON serialization
            if "published" in item_copy and item_copy["published"]:
                if isinstance(item_copy["published"], datetime):
                    item_copy["published"] = _dt_to_str(item_copy["published"])
                elif isinstance(item_copy["published"], str):
                    # Already a string, ensure it's in the correct format
                    try:
                        # Parse and reformat to ensure consistency
                        dt = _str_to_dt(item_copy["published"])
                        item_copy["published"] = _dt_to_str(dt)
                    except ValueError:
                        # If parsing fails, leave as is
                        pass
            
            existing_items[item_id] = item_copy
        
        # For items with same published time, we need to sort by item_id ascending
        # Group items by published time
        from collections import defaultdict
        time_groups = defaultdict(list)
        for item in existing_items.values():
            # Parse published time for grouping
            if isinstance(item["published"], str):
                time_key = _str_to_dt(item["published"])
            else:
                time_key = item["published"]
            time_groups[time_key].append(item)
        
        # Sort within each time group by item_id
        sorted_items = []
        for time_key in sorted(time_groups.keys(), reverse=True):
            group_items = sorted(time_groups[time_key], key=lambda x: x["item_id"])
            sorted_items.extend(group_items)
        
        # Convert datetime to string for JSON serialization
        for item in sorted_items:
            if "published" in item and item["published"]:
                if isinstance(item["published"], datetime):
                    item["published"] = _dt_to_str(item["published"])
                elif isinstance(item["published"], str):
                    # Already a string, ensure it's in the correct format
                    try:
                        # Parse and reformat to ensure consistency
                        dt = _str_to_dt(item["published"])
                        item["published"] = _dt_to_str(dt)
                    except ValueError:
                        # If parsing fails, leave as is
                        pass
        
        # Save to file
        data = {"items": sorted_items}
        
        # Ensure parent directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
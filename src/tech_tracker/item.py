from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any


@dataclass(frozen=True, slots=True)
class Item:
    item_id: str
    source_type: str
    source_url: str
    title: str
    link: str
    published: datetime  # Must be timezone-aware UTC

    def to_dict(self) -> Dict[str, Any]:
        """Convert Item to dictionary, with published as Z-format string."""
        # Convert to UTC first, then format with microsecond precision
        published_utc = self.published.astimezone(timezone.utc)
        return {
            "item_id": self.item_id,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "title": self.title,
            "link": self.link,
            "published": published_utc.isoformat().replace("+00:00", "Z"),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Item":
        """Create Item from dictionary.
        
        Supports:
        - d["published"] as "....Z" string (with or without microseconds)
        - d["published"] as timezone-aware datetime (optional)
        """
        # Check required fields
        required_fields = ["item_id", "source_type", "source_url", "title", "link", "published"]
        for field in required_fields:
            if field not in d:
                raise KeyError(f"Missing required field: '{field}'")
        
        published_raw = d["published"]
        
        if isinstance(published_raw, str):
            # Parse "....Z" string to UTC datetime
            if not published_raw.endswith("Z"):
                raise ValueError(f"Published datetime must end with 'Z': {published_raw}")
            
            # Remove Z and replace with +00:00 for fromisoformat
            published_str = published_raw[:-1] + "+00:00"
            try:
                published = datetime.fromisoformat(published_str)
                # Ensure UTC
                published = published.astimezone(timezone.utc)
            except ValueError as e:
                raise ValueError(f"Invalid datetime format: {published_raw}") from e
        elif isinstance(published_raw, datetime):
            if published_raw.tzinfo is None:
                raise ValueError("Published datetime must be timezone-aware")
            published = published_raw.astimezone(timezone.utc)
        else:
            raise TypeError(f"Published must be str or datetime, got {type(published_raw)}")
        
        return cls(
            item_id=d["item_id"],
            source_type=d["source_type"],
            source_url=d["source_url"],
            title=d["title"],
            link=d["link"],
            published=published,
        )
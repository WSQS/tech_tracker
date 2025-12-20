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
        # Convert to UTC first, then format
        published_utc = self.published.astimezone(timezone.utc)
        return {
            "item_id": self.item_id,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "title": self.title,
            "link": self.link,
            "published": published_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Item":
        """Create Item from dictionary.
        
        Supports:
        - d["published"] as "....Z" string (required)
        - d["published"] as timezone-aware datetime (optional)
        """
        published_raw = d["published"]
        
        if isinstance(published_raw, str):
            # Parse "....Z" string to UTC datetime using strptime
            if not published_raw.endswith("Z"):
                raise ValueError(f"Published datetime must end with 'Z': {published_raw}")
            
            try:
                published = datetime.strptime(published_raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
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
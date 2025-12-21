"""Recommender interface and implementations."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Protocol

from tech_tracker.item import Item


@dataclass(frozen=True, slots=True)
class RecommendRequest:
    """Request for recommendation.
    
    Attributes:
        items: List of items to recommend from.
        limit: Maximum number of items to recommend.
        context: Additional context for recommendation strategies.
    """
    items: List[Item]
    limit: int = 20
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RecommendResult:
    """Result of recommendation.
    
    Attributes:
        items: List of recommended items.
        meta: Metadata about the recommendation.
    """
    items: List[Item]
    meta: Dict[str, Any] = field(default_factory=dict)


class Recommender(Protocol):
    """Interface for recommendation strategies."""
    
    def recommend(self, req: RecommendRequest) -> RecommendResult:
        """Generate recommendations based on the request.
        
        Args:
            req: Recommendation request containing items and parameters.
            
        Returns:
            Recommendation result with items and metadata.
        """
        ...
    
    @property
    def name(self) -> str:
        """Get the name of the recommender strategy."""
        ...


class LatestRecommender:
    """Default recommender that returns latest items by published time."""
    
    def __init__(self) -> None:
        """Initialize the LatestRecommender."""
        pass
    
    @property
    def name(self) -> str:
        """Get the name of the recommender."""
        return "latest"
    
    def recommend(self, req: RecommendRequest) -> RecommendResult:
        """Recommend latest items sorted by published time.
        
        Args:
            req: Recommendation request.
            
        Returns:
            Recommendation result with latest items.
        """
        # Sort by published descending, then item_id ascending
        sorted_items = sorted(
            req.items,
            key=lambda item: (-item.published.timestamp(), item.item_id)
        )
        
        # Apply limit
        limited_items = sorted_items[:req.limit]
        
        # Create result with metadata
        meta = {
            "strategy": "latest",
            "limit": req.limit,
        }
        
        return RecommendResult(items=limited_items, meta=meta)


def recommend_from_store(
    store: "JsonItemStore",
    recommender: Recommender,
    limit: int = 20,
    context: Dict[str, Any] | None = None,
) -> RecommendResult:
    """Generate recommendations from a JsonItemStore.
    
    Args:
        store: JsonItemStore instance to load items from.
        recommender: Recommender strategy to use.
        limit: Maximum number of items to recommend.
        context: Additional context for recommendation strategies.
        
    Returns:
        Recommendation result with items and metadata.
    """
    # Load items from store
    items = store.load_all()
    
    # Create recommendation request
    req = RecommendRequest(items=items, limit=limit, context=context or {})
    
    # Get recommendation
    result = recommender.recommend(req)
    
    # Enhance metadata with store and recommender info
    enhanced_meta = dict(result.meta)  # Copy existing meta
    enhanced_meta.update({
        "source": "store",
        "recommender": recommender.name,
    })
    
    # Return new result with enhanced metadata
    return RecommendResult(items=result.items, meta=enhanced_meta)


def render_recommendation_markdown(result: RecommendResult) -> str:
    """Render recommendation result as Markdown.
    
    Args:
        result: Recommendation result to render.
        
    Returns:
        Markdown string representation of the recommendation.
    """
    from datetime import timezone
    
    lines = []
    
    # 1) First line: "# Recommended Items"
    lines.append("# Recommended Items")
    
    # 2) Second line: empty line
    lines.append("")
    
    # 3) Meta information (strategy and limit only)
    if result.meta:
        if "strategy" in result.meta:
            lines.append(f"_Strategy_: {result.meta['strategy']}")
        if "limit" in result.meta:
            lines.append(f"_Limit_: {result.meta['limit']}")
        # Add empty line after meta if any meta was rendered
        if "strategy" in result.meta or "limit" in result.meta:
            lines.append("")
    
    # 4) Items sections
    for index, item in enumerate(result.items, 1):
        # Section title
        lines.append(f"## {index}. {item.title}")
        
        # Format published time with Z suffix
        published_iso_z = item.published.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Bullet points
        lines.append(f"- Source: {item.source_type}")
        lines.append(f"- Channel: {item.source_url}")
        lines.append(f"- Published: {published_iso_z}")
        lines.append(f"- Link: {item.link}")
        
        # Empty line after each item section
        lines.append("")
    
    # Join with newlines and ensure trailing newline
    result = "\n".join(lines)
    if not result.endswith("\n\n"):
        result += "\n"
    return result
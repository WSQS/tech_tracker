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
        
        Filters out seen items when unseen items are available.
        Falls back to all items when all items are seen.
        
        Args:
            req: Recommendation request.
            
        Returns:
            Recommendation result with latest items.
        """
        # Filter unseen items
        unseen_items = [item for item in req.items if not item.seen]
        
        # Use unseen items if available, otherwise use all items (fallback)
        items_to_process = unseen_items if unseen_items else req.items
        
        # Sort by published descending, then item_id ascending
        sorted_items = sorted(
            items_to_process,
            key=lambda item: (-item.published.timestamp(), item.item_id)
        )
        
        # Apply limit
        limited_items = sorted_items[:req.limit]
        
        # Create result with metadata
        meta = {
            "strategy": "latest",
            "limit": req.limit,
            "filtered": len(unseen_items) > 0,  # Whether filtering was applied
            "total_items": len(req.items),
            "unseen_items": len(unseen_items),
        }
        
        return RecommendResult(items=limited_items, meta=meta)


class KeywordFromSeenRecommender:
    """Recommender that suggests items based on keywords from seen items."""
    
    def __init__(self) -> None:
        """Initialize the KeywordFromSeenRecommender."""
        pass
    
    @property
    def name(self) -> str:
        """Get the name of the recommender."""
        return "keyword_from_seen"
    
    def recommend(self, req: RecommendRequest) -> RecommendResult:
        """Recommend items based on keywords extracted from seen items.
        
        Uses the recommend_keyword_from_seen pure function for the core logic.
        
        Args:
            req: Recommendation request containing items and parameters.
            
        Returns:
            Recommendation result with keyword-based suggestions.
        """
        # Use the pure function for core recommendation logic
        recommended_items = recommend_keyword_from_seen(req.items, req.limit)
        
        # Create result with metadata
        meta = {
            "strategy": "keyword_from_seen",
            "limit": req.limit,
            "total_items": len(req.items),
        }
        
        return RecommendResult(items=recommended_items, meta=meta)


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
    
    # 1) Meta information (strategy and limit only)
    if result.meta:
        if "strategy" in result.meta:
            lines.append(f"_Strategy_: {result.meta['strategy']}")
        if "limit" in result.meta:
            lines.append(f"_Limit_: {result.meta['limit']}")
        # Add empty line after meta if any meta was rendered
        if "strategy" in result.meta or "limit" in result.meta:
            lines.append("")
    
    # 2) Items sections
    for index, item in enumerate(result.items, 1):
        # Section title
        lines.append(f"## {index}. {item.title}")
        
        # Format published time with Z suffix
        published_iso_z = item.published.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Bullet points
        lines.append(f"- ID: `{item.item_id}`")
        lines.append(f"- Source: {item.source_type}")
        lines.append(f"- Channel: {item.source_url}")
        lines.append(f"- Published: {published_iso_z}")
        lines.append(f"- Link: {item.link}")
        
        # Empty line after each item section
        lines.append("")
    
    # Join with newlines and ensure trailing newline if there's content
    if not lines:
        return ""
    
    result = "\n".join(lines)
    if not result.endswith("\n\n"):
        result += "\n"
    return result


def recommend_keyword_from_seen(
    items: List[Item],
    limit: int = 20
) -> List[Item]:
    """Recommend items based on keywords extracted from seen items.
    
    This pure function implements keyword-based recommendation:
    1. Extract keywords from seen items' titles
    2. Calculate keyword weights based on frequency
    3. Score candidate items based on keyword overlap
    4. Sort by score (desc), published (desc), item_id (asc)
    5. Apply limit
    
    Args:
        items: List of items to recommend from.
        limit: Maximum number of items to recommend (default: 20).
        
    Returns:
        List of recommended items sorted by relevance.
    """
    from collections import Counter
    import re
    
    # Helper function to tokenize title
    def tokenize_title(title: str) -> List[str]:
        """Split title into tokens by non-alphanumeric characters.
        
        Args:
            title: The title string to tokenize.
            
        Returns:
            List of lowercase tokens, with empty strings filtered out.
        """
        # Split by non-alphanumeric characters
        tokens = re.split(r'[^a-zA-Z0-9]', title)
        # Convert to lowercase and filter out empty strings
        return [token.lower() for token in tokens if token]
    
    # 1. Extract keywords from seen items
    seen_items = [item for item in items if item.seen]
    keyword_counts = Counter()
    
    for item in seen_items:
        tokens = tokenize_title(item.title)
        keyword_counts.update(tokens)
    
    # If no seen items, return empty list
    if not keyword_counts:
        return []
    
    # 2. Determine candidate items
    unseen_items = [item for item in items if not item.seen]
    candidate_items = unseen_items if unseen_items else items
    
    # 3. Score candidate items
    scored_items = []
    for item in candidate_items:
        tokens = tokenize_title(item.title)
        # Score = sum of keyword weights for tokens that appear in seen keywords
        score = sum(keyword_counts[token] for token in tokens if token in keyword_counts)
        scored_items.append((item, score))
    
    # 4. Sort by score (desc), published (desc), item_id (asc)
    scored_items.sort(
        key=lambda x: (
            -x[1],  # score descending
            -x[0].published.timestamp(),  # published descending
            x[0].item_id  # item_id ascending
        )
    )
    
    # 5. Apply limit
    recommended_items = [item for item, score in scored_items[:limit]]
    
    return recommended_items